"""Version-controlled JSON projection for governed authored course content.

The knowledge pool remains the runtime source of truth.  This module mirrors only
Agent-editable authored fields and deliberately never calls content.delete().
Git transport is outside this module: callers pass a local checkout path.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from workbench.data import content, difficulty as difficulty_data, figure_mirror


SCHEMA_VERSION = 1
ENTITY_DIRS = {
    "kp": "knowledge",
    "problem": "problems",
    "relation": "relations",
}
PROBLEM_DIFFICULTY_DIMENSIONS = {
    "difficulty_knowledge_breadth": "knowledge_breadth",
    "difficulty_reasoning_depth": "reasoning_depth",
    "difficulty_transfer_distance": "transfer_distance",
    "difficulty_construction_openness": "construction_openness",
}
PROBLEM_DIFFICULTY_COLUMNS = (
    "difficulty", *PROBLEM_DIFFICULTY_DIMENSIONS, "difficulty_model",
)
PROBLEM_DIFFICULTY_FIELDS = set(PROBLEM_DIFFICULTY_COLUMNS)
# Mirror the governed authored CRUD surface plus the separately governed problem
# difficulty rating and logical figure references. Runtime/learner rows and
# batch/timestamp metadata stay local.
MIRROR_FIELDS = {
    entity_type: set(fields) for entity_type, fields in content.EDITABLE_FIELDS.items()
}
MIRROR_FIELDS["kp"].add("figure_paths")
MIRROR_FIELDS["problem"].update(PROBLEM_DIFFICULTY_FIELDS)
ARRAY_FIELDS = {
    "kp": {"related_kp_ids", "figure_paths"},
    "problem": {"kp_ids", "practice_modes", "figure_paths"},
}
OBJECT_FIELDS = {"problem": {"micro_quiz"}}
EMPTY_JSON_DEFAULTS = {
    "kp": {"related_kp_ids": [], "figure_paths": None},
    "problem": {
        "kp_ids": [], "practice_modes": None, "micro_quiz": None,
        "figure_paths": None,
    },
}
ENVELOPE_FIELDS = {
    "schema_version", "entity_type", "entity_id", "revision", "content",
}
DELETE_FIELDS = {
    "schema_version", "request_id", "course_id", "entity_type", "entity_id", "reason",
}
SYNC_DIRECTIONS = {
    "init", "repo_to_pool", "pool_to_repo", "restore_repo_file", "recover_converged",
}


class MirrorError(ValueError):
    """A readable contract failure for one repository or entity."""


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _pretty_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _require_tables(pool):
    names = {
        row[0] for row in pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    missing = {"content_mirror_state", "content_mirror_log"} - names
    if missing:
        raise MirrorError(
            "content mirror schema is missing — run the current Lesson Kit pool schema migration"
        )


def _course_root(repo, course):
    return Path(repo).resolve() / "courses" / course


def entity_path(repo, course, entity_type, entity_id):
    try:
        directory = ENTITY_DIRS[entity_type]
    except KeyError as exc:
        raise MirrorError(f"unsupported mirror entity type: {entity_type}") from exc
    return _course_root(repo, course) / directory / f"{entity_id}.json"


def _atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(_pretty_json(value), encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _envelope(entity_type, entity_id, revision, authored):
    return {
        "schema_version": SCHEMA_VERSION,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "revision": revision,
        "content": authored,
    }


def _validate_id(course, entity_id):
    if not isinstance(entity_id, str) or not entity_id:
        raise MirrorError("entity_id must be a non-empty string")
    if not entity_id.startswith(course + "-"):
        raise MirrorError(f"entity_id must belong to course {course}: {entity_id}")


def _load_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise MirrorError(f"invalid JSON in {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise MirrorError(f"JSON is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise MirrorError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MirrorError(f"JSON document must be an object: {path}")
    return value


def read_entity(path, course, expected_type=None):
    value = _load_json(path)
    unknown = sorted(set(value) - ENVELOPE_FIELDS)
    missing = sorted(ENVELOPE_FIELDS - set(value))
    if unknown:
        raise MirrorError(f"unsupported envelope field(s): {', '.join(unknown)}")
    if missing:
        raise MirrorError(f"missing envelope field(s): {', '.join(missing)}")
    version = value["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != SCHEMA_VERSION:
        raise MirrorError(
            f"unsupported schema_version {version!r}; expected integer {SCHEMA_VERSION}"
        )
    entity_type = value["entity_type"]
    if not isinstance(entity_type, str) or entity_type not in ENTITY_DIRS:
        raise MirrorError(f"unsupported mirror entity type: {entity_type}")
    if expected_type and entity_type != expected_type:
        raise MirrorError(
            f"entity_type {entity_type!r} does not match directory type {expected_type!r}"
        )
    _validate_id(course, value["entity_id"])
    revision = value["revision"]
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise MirrorError("revision must be a positive integer")
    authored = value["content"]
    if not isinstance(authored, dict):
        raise MirrorError("content must be a JSON object")
    allowed = MIRROR_FIELDS[entity_type]
    unsupported = sorted(set(authored) - allowed)
    if unsupported:
        raise MirrorError(
            f"unsupported {entity_type} content field(s): {', '.join(unsupported)}"
        )
    for field in ARRAY_FIELDS.get(entity_type, ()):
        if field in authored and authored[field] is not None and not isinstance(authored[field], list):
            raise MirrorError(f"{entity_type}.{field} must be a JSON array or null")
    for field in OBJECT_FIELDS.get(entity_type, ()):
        if field in authored and authored[field] is not None and not isinstance(authored[field], dict):
            raise MirrorError(f"{entity_type}.{field} must be a JSON object or null")
    return value


def authored_projection(row, entity_type):
    if row is None:
        return None
    defaults = EMPTY_JSON_DEFAULTS.get(entity_type, {})
    arrays = ARRAY_FIELDS.get(entity_type, ())
    projected = {}
    for field in sorted(MIRROR_FIELDS[entity_type]):
        if field not in row:
            continue
        value = row[field]
        if value == "" and field in defaults:
            value = defaults[field]
        elif field in arrays and isinstance(value, str):
            value = json.loads(value) if value else defaults.get(field)
        projected[field] = value
    return projected


def pool_projection(pool, entity_type, entity_id):
    return authored_projection(content.get(pool, entity_type, entity_id), entity_type)


def _all_pool_entities(pool):
    identity_fields = {"kp": "kp_id", "problem": "problem_id", "relation": "relation_id"}
    for entity_type in ENTITY_DIRS:
        for row in content.list_items(pool, entity_type):
            identity = row[identity_fields[entity_type]]
            if str(identity).startswith(pool.course + "-"):
                yield entity_type, identity, authored_projection(row, entity_type)


def _state(pool, entity_type, entity_id):
    row = pool.connect().execute(
        "SELECT revision, content_json FROM content_mirror_state "
        "WHERE entity_type=? AND entity_id=?",
        (entity_type, entity_id),
    ).fetchone()
    if row is None:
        return None
    try:
        authored = json.loads(row["content_json"])
    except json.JSONDecodeError as exc:
        raise MirrorError(f"stored mirror state is corrupt for {entity_id}") from exc
    return {"revision": int(row["revision"]), "content": authored}


def _put_state(pool, entity_type, entity_id, revision, authored, direction):
    if direction not in SYNC_DIRECTIONS:
        raise MirrorError(f"unsupported synchronization direction: {direction}")
    with pool.transaction():
        conn = pool.connect()
        previous = conn.execute(
            "SELECT revision FROM content_mirror_state WHERE entity_type=? AND entity_id=?",
            (entity_type, entity_id),
        ).fetchone()
        previous_revision = int(previous[0]) if previous else None
        conn.execute(
            "INSERT INTO content_mirror_state "
            "(entity_type, entity_id, revision, content_json, updated_at) "
            "VALUES (?, ?, ?, ?, datetime('now')) "
            "ON CONFLICT(entity_type, entity_id) DO UPDATE SET "
            "revision=excluded.revision, content_json=excluded.content_json, "
            "updated_at=datetime('now')",
            (entity_type, entity_id, revision, _json_text(authored)),
        )
        conn.execute(
            "INSERT INTO content_mirror_log "
            "(entity_type, entity_id, direction, from_revision, to_revision) "
            "VALUES (?, ?, ?, ?, ?)",
            (entity_type, entity_id, direction, previous_revision, revision),
        )


def _tracked(pool, entity_id=None):
    sql = "SELECT entity_type, entity_id FROM content_mirror_state"
    params = ()
    if entity_id:
        sql += " WHERE entity_id=?"
        params = (entity_id,)
    sql += " ORDER BY entity_type, entity_id"
    return [tuple(row) for row in pool.connect().execute(sql, params)]


def _scan_repo(repo, course):
    found = {}
    ambiguous = set()
    errors = []
    root = _course_root(repo, course)
    if not root.exists():
        return found, errors
    directories = {
        directory: entity_type for entity_type, directory in ENTITY_DIRS.items()
    }
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        directory = relative.parts[0] if len(relative.parts) > 1 else None
        entity_type = directories.get(directory)
        if entity_type and path.suffix == ".json":
            try:
                envelope = read_entity(path, course, entity_type)
                key = (entity_type, envelope["entity_id"])
                if key in found or key in ambiguous:
                    found.pop(key, None)
                    ambiguous.add(key)
                    errors.append({
                        "path": str(path), "status": "invalid",
                        "entity_type": entity_type,
                        "entity_id": envelope["entity_id"],
                        "error": f"duplicate entity_id: {envelope['entity_id']}",
                    })
                    continue
                found[key] = (path, envelope)
            except MirrorError as exc:
                errors.append({"path": str(path), "status": "invalid", "error": str(exc)})
            continue
        try:
            text = path.read_bytes().decode("utf-8-sig")
            if path.suffix == ".json":
                value = json.loads(text)
                if not isinstance(value, dict):
                    raise MirrorError(f"JSON document must be an object: {path}")
        except MirrorError as exc:
            errors.append({"path": str(path), "status": "invalid", "error": str(exc)})
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append({
                "path": str(path), "status": "invalid",
                "error": f"cannot be read as UTF-8 JSON text: {path} ({exc})",
            })
    return found, errors


def _read_delete_requests(repo, course):
    folder = Path(repo).resolve() / "delete-requests"
    items = []
    if not folder.exists():
        return items
    for path in sorted(folder.glob("*.json")):
        try:
            value = _load_json(path)
            target = value.get("course_id")
            if isinstance(target, str) and target != course:
                continue
            unknown = sorted(set(value) - DELETE_FIELDS)
            missing = sorted(DELETE_FIELDS - set(value))
            if unknown or missing:
                details = []
                if unknown:
                    details.append("unsupported field(s): " + ", ".join(unknown))
                if missing:
                    details.append("missing field(s): " + ", ".join(missing))
                raise MirrorError("; ".join(details))
            version = value["schema_version"]
            if isinstance(version, bool) or not isinstance(version, int) \
                    or version != SCHEMA_VERSION:
                raise MirrorError("unsupported deletion-request schema_version")
            if value["course_id"] != course:
                continue
            if not isinstance(value["entity_type"], str) \
                    or value["entity_type"] not in ENTITY_DIRS:
                raise MirrorError("unsupported deletion-request entity_type")
            _validate_id(course, value["entity_id"])
            if not isinstance(value["request_id"], str) or not value["request_id"]:
                raise MirrorError("request_id must be a non-empty string")
            if not isinstance(value["reason"], str):
                raise MirrorError("reason must be a string")
            items.append({
                "path": str(path), "status": "pending_non_executing", **value,
            })
        except MirrorError as exc:
            items.append({"path": str(path), "status": "invalid", "error": str(exc)})
    return items


def _unreadable_texts(parse_errors):
    items = []
    for error in parse_errors:
        if error.get("entity_id"):
            continue
        path = Path(error["path"])
        try:
            text = path.read_bytes().decode("utf-8", "replace")
        except OSError:
            text = ""
        items.append((path, text))
    return items


def _implicating_path(unreadable, identity):
    for path, text in unreadable:
        if identity in path.name or identity in text:
            return path
    return None


def init(pool, repo, entity_id=None, dry_run=False):
    """Pool-first bootstrap. Existing matching files are adopted; conflicts are refused."""
    _require_tables(pool)
    repo = Path(repo).resolve()
    found, parse_errors = _scan_repo(repo, pool.course)
    unreadable = _unreadable_texts(parse_errors)
    results = list(parse_errors)
    for entity_type, identity, authored in _all_pool_entities(pool):
        if entity_id and identity != entity_id:
            continue
        if _state(pool, entity_type, identity):
            results.append(_result(entity_type, identity, "noop", "already_tracked"))
            continue
        path = entity_path(repo, pool.course, entity_type, identity)
        duplicate = next((error for error in parse_errors
                          if error.get("entity_type") == entity_type
                          and error.get("entity_id") == identity), None)
        if duplicate:
            results.append(_result(
                entity_type, identity, "invalid", duplicate["error"], path=duplicate["path"],
            ))
            continue
        existing_entry = found.get((entity_type, identity))
        existing_path, existing = existing_entry if existing_entry else (path, None)
        if existing is None:
            implicating = _implicating_path(unreadable, identity)
            if implicating is not None:
                results.append(_result(
                    entity_type, identity, "invalid",
                    f"an unreadable repository file may already name this entity: {implicating}",
                    path=implicating,
                ))
                continue
        if existing is None and existing_path.exists():
            try:
                existing = read_entity(existing_path, pool.course, entity_type)
                if existing["entity_id"] != identity:
                    results.append(_result(
                        entity_type, identity, "invalid",
                        "entity identity mismatch at its canonical path", path=existing_path,
                    ))
                    continue
            except MirrorError as exc:
                results.append(_result(entity_type, identity, "invalid", str(exc), path=existing_path))
                continue
        if existing is not None:
            if existing["revision"] != 1 or existing["content"] != authored:
                results.append(_result(
                    entity_type, identity, "conflict",
                    "existing JSON does not match pool bootstrap content",
                    path=existing_path,
                ))
                continue
        if not dry_run:
            try:
                if existing is None:
                    _atomic_write(path, _envelope(entity_type, identity, 1, authored))
                _put_state(pool, entity_type, identity, 1, authored, "init")
            except (MirrorError, ValueError, KeyError, sqlite3.Error, OSError) as exc:
                results.append(_result(
                    entity_type, identity, "invalid", f"bootstrap write failed: {exc}",
                    path=existing_path if existing is not None else path,
                ))
                continue
        results.append(_result(
            entity_type, identity, "initialized", revision=1,
            path=existing_path if existing is not None else path,
        ))
    if entity_id and not any(item.get("entity_id") == entity_id for item in results):
        results.append({"entity_id": entity_id, "status": "invalid", "error": "entity is not in this pool"})
    return _report(results, _read_delete_requests(repo, pool.course))


def _result(entity_type, entity_id, status, detail=None, revision=None, path=None):
    result = {"entity_type": entity_type, "entity_id": entity_id, "status": status}
    if detail:
        result["detail"] = detail
    if revision is not None:
        result["revision"] = revision
    if path is not None:
        result["path"] = str(path)
    return result


def _align_projection(baseline, pool_now, incoming):
    """Adopt newly mirrored pool fields without invalidating an older v1 ledger/file."""
    baseline_fields = set(baseline)
    pool_fields = set(pool_now)
    incoming_fields = set(incoming)
    missing = sorted(baseline_fields - incoming_fields)
    if missing:
        return baseline, incoming, False, (
            "content fields cannot remove initialized field(s): " + ", ".join(missing)
        )
    unavailable = sorted(incoming_fields - (baseline_fields | pool_fields))
    if unavailable:
        return baseline, incoming, False, (
            "content field(s) are unavailable in this pool schema: " + ", ".join(unavailable)
        )
    added = pool_fields - baseline_fields
    effective_baseline = {
        **baseline,
        **{field: pool_now[field] for field in added},
    }
    effective_incoming = {**effective_baseline, **incoming}
    return effective_baseline, effective_incoming, bool(added), None


def _plan_one(pool, repo_entry, entity_type, entity_id):
    state = _state(pool, entity_type, entity_id)
    if state is None:
        return _result(
            entity_type, entity_id, "invalid",
            "entity is not initialized in mirror state; run mirror init",
        )
    baseline = state["content"]
    revision = state["revision"]
    pool_now = pool_projection(pool, entity_type, entity_id)
    if pool_now is None:
        return _result(
            entity_type, entity_id, "conflict",
            "tracked pool row is missing; repository synchronization never deletes or recreates it implicitly",
            revision,
        )
    newly_projected_fields = set(pool_now) - set(baseline)
    if entity_type in {"kp", "problem"}:
        try:
            figure_mirror.validate_references(
                pool.course, pool_now.get("figure_paths"), entity_id,
            )
            if repo_entry is not None:
                figure_mirror.validate_references(
                    pool.course, repo_entry[1]["content"].get("figure_paths"), entity_id,
                )
        except figure_mirror.FigureMirrorError as exc:
            return _result(entity_type, entity_id, "invalid", str(exc), revision)
    if repo_entry is None:
        return _result(entity_type, entity_id, "restore_repo_file", revision=revision + 1)

    path, envelope = repo_entry
    if envelope["entity_id"] != entity_id:
        return _result(entity_type, entity_id, "invalid", "entity identity mismatch", path=path)
    baseline, incoming, projection_upgrade, error = _align_projection(
        baseline, pool_now, envelope["content"]
    )
    if error:
        return _result(entity_type, entity_id, "invalid", error, revision, path=path)
    repo_now, error = _normalise_incoming(
        pool, entity_type, entity_id, baseline, incoming,
    )
    if error:
        return _result(entity_type, entity_id, "invalid", error, revision, path=path)
    repo_revision = envelope["revision"]
    pool_changed = pool_now != baseline
    repo_changed = repo_now != baseline
    present_new_fields = newly_projected_fields & set(envelope["content"])
    if present_new_fields and present_new_fields != newly_projected_fields:
        return _result(
            entity_type, entity_id, "invalid",
            "projection upgrade must include every newly available field",
            revision, path=path,
        )
    if present_new_fields and any(
        repo_now[field] != pool_now[field] for field in present_new_fields
    ):
        return _result(
            entity_type, entity_id, "conflict",
            "newly projected fields differ from the current pool projection",
            revision, path=path,
        )
    if not repo_changed:
        if repo_revision != revision:
            if (
                projection_upgrade
                and repo_revision == revision + 1
                and set(pool_now) <= set(envelope["content"])
                and repo_now == pool_now
            ):
                return _result(
                    entity_type, entity_id, "recover_converged",
                    revision=repo_revision, path=path,
                )
            return _result(
                entity_type, entity_id, "invalid",
                f"unchanged content must keep revision {revision}", revision, path=path,
            )
        if present_new_fields:
            return _result(
                entity_type, entity_id, "invalid",
                f"new projection fields must advance revision {revision} -> {revision + 1}",
                revision, path=path,
            )
        if pool_changed or projection_upgrade:
            return _result(
                entity_type, entity_id, "pool_to_repo", revision=revision + 1, path=path
            )
        return _result(entity_type, entity_id, "noop", revision=revision, path=path)

    if repo_revision != revision + 1:
        return _result(
            entity_type, entity_id, "invalid",
            f"changed repository content must advance revision {revision} -> {revision + 1}",
            revision, path=path,
        )
    if not pool_changed:
        return _result(entity_type, entity_id, "repo_to_pool", revision=repo_revision, path=path)
    if pool_now == repo_now:
        return _result(
            entity_type, entity_id, "recover_converged", revision=repo_revision, path=path
        )
    return _result(
        entity_type, entity_id, "conflict",
        "pool and repository both changed differently from the synchronized content",
        revision, path=path,
    )


def _normalise_problem_difficulty(pool, entity_id, baseline, incoming, changed):
    dimension_columns = set(PROBLEM_DIFFICULTY_DIMENSIONS)
    if changed & {"difficulty", "difficulty_model"} and not changed & dimension_columns:
        return None, (
            "difficulty and difficulty_model are derived; edit the four difficulty dimensions"
        )
    available = set(baseline) & PROBLEM_DIFFICULTY_FIELDS
    dimensions = {
        column: incoming.get(column) for column in PROBLEM_DIFFICULTY_DIMENSIONS
    }
    if all(value is None for value in dimensions.values()):
        return {
            field: None for field in PROBLEM_DIFFICULTY_COLUMNS if field in available
        }, None
    if available != PROBLEM_DIFFICULTY_FIELDS:
        return None, "the complete difficulty group is unavailable in this pool schema"
    if any(value is None for value in dimensions.values()):
        return None, "difficulty dimensions must be all null or all present"
    vector = {
        rule_name: dimensions[column]
        for column, rule_name in PROBLEM_DIFFICULTY_DIMENSIONS.items()
    }
    try:
        checked = difficulty_data.check(pool, {"items": [{"problem_id": entity_id, **vector}]})
    except ValueError as exc:
        return None, str(exc)
    item = checked["items"][0]
    return {
        **{
            column: item[rule_name]
            for column, rule_name in PROBLEM_DIFFICULTY_DIMENSIONS.items()
        },
        "difficulty": item["difficulty"],
        "difficulty_model": item["difficulty_model"],
    }, None


def _normalise_incoming(pool, entity_type, entity_id, baseline, incoming):
    patch = {key: incoming[key] for key in incoming if incoming[key] != baseline[key]}
    if not patch:
        return incoming, None
    if entity_type == "problem":
        difficulty_changed = set(patch) & PROBLEM_DIFFICULTY_FIELDS
        content_patch = {
            key: value for key, value in patch.items()
            if key not in PROBLEM_DIFFICULTY_FIELDS
        }
        if content_patch:
            plan = content.plan_problem_update(pool, entity_id, content_patch)
            if plan["errors"]:
                return incoming, "; ".join(plan["errors"])
            normalized = {**baseline, **plan["fields"]}
            clears_difficulty = plan["clear_difficulty"]
        else:
            normalized = dict(baseline)
            clears_difficulty = False
        if difficulty_changed:
            rating, error = _normalise_problem_difficulty(
                pool, entity_id, baseline, incoming, difficulty_changed,
            )
            if error:
                return incoming, error
            normalized.update(rating)
        elif clears_difficulty:
            normalized.update({
                field: None for field in PROBLEM_DIFFICULTY_COLUMNS if field in baseline
            })
        return normalized, None
    elif entity_type == "relation":
        from workbench.data import relations
        result = relations.check(pool, {"items": [{
            "action": "update", "relation_id": entity_id, **patch,
        }]})
        if not result["valid"]:
            return incoming, "; ".join(item["message"] for item in result["errors"])
    return incoming, None


def plan(pool, repo, entity_id=None):
    _require_tables(pool)
    repo = Path(repo).resolve()
    found, parse_errors = _scan_repo(repo, pool.course)
    results = list(parse_errors)
    tracked = _tracked(pool, entity_id)
    tracked_keys = set(tracked)
    for entity_type, identity in tracked:
        repo_entry = found.get((entity_type, identity))
        if repo_entry is None and parse_errors:
            results.append(_result(
                entity_type, identity, "invalid",
                "repository contains unreadable or duplicate entity JSON; "
                "refusing missing-file restoration until it is repaired",
            ))
            continue
        if repo_entry is None:
            canonical = entity_path(repo, pool.course, entity_type, identity)
            if canonical.exists():
                try:
                    envelope = read_entity(canonical, pool.course, entity_type)
                except MirrorError as exc:
                    results.append(_result(entity_type, identity, "invalid", str(exc), path=canonical))
                    continue
                if envelope["entity_id"] != identity:
                    results.append(_result(
                        entity_type, identity, "invalid",
                        "entity identity mismatch at its canonical path", path=canonical,
                    ))
                    continue
        results.append(_plan_one(pool, repo_entry, entity_type, identity))
    for (entity_type, identity), (path, _envelope_value) in sorted(found.items()):
        if entity_id and identity != entity_id:
            continue
        if (entity_type, identity) not in tracked_keys:
            results.append(_result(
                entity_type, identity, "invalid",
                "repository-only entity is not tracked; remote creation is not enabled in v1",
                path=path,
            ))
    if entity_id and not any(item.get("entity_id") == entity_id for item in results):
        results.append({"entity_id": entity_id, "status": "invalid", "error": "entity is not tracked"})
    return _report(results, _read_delete_requests(repo, pool.course))


def _apply_problem_patch(pool, entity_id, patch, authored):
    difficulty_changed = bool(set(patch) & PROBLEM_DIFFICULTY_FIELDS)
    content_patch = {
        key: value for key, value in patch.items() if key not in PROBLEM_DIFFICULTY_FIELDS
    }
    if "figure_paths" in content_patch and content_patch["figure_paths"] is not None:
        content_patch["figure_paths"] = json.dumps(
            content_patch["figure_paths"], ensure_ascii=False
        )
    if content_patch:
        content.update(pool, "problem", entity_id, content_patch)
    if difficulty_changed:
        columns = [field for field in PROBLEM_DIFFICULTY_COLUMNS if field in authored]
        cursor = pool.connect().execute(
            "UPDATE problems SET " + ", ".join(f"{column}=?" for column in columns)
            + " WHERE problem_id=?",
            tuple(authored.get(column) for column in columns) + (entity_id,),
        )
        if cursor.rowcount == 0:
            raise KeyError(entity_id)


def _apply_kp_patch(pool, entity_id, patch):
    content_patch = dict(patch)
    figure_paths = content_patch.pop("figure_paths", ...)
    if content_patch:
        content.update(pool, "kp", entity_id, content_patch)
    if figure_paths is ...:
        return
    columns = {row[1] for row in pool.connect().execute("PRAGMA table_info(knowledge_points)")}
    if "figure_paths" not in columns:
        raise MirrorError("knowledge_points.figure_paths is unavailable in this pool schema")
    assignments = ["figure_paths=?"]
    if "updated_at" in columns:
        assignments.append("updated_at=datetime('now')")
    value = None if figure_paths is None else json.dumps(figure_paths, ensure_ascii=False)
    cursor = pool.connect().execute(
        f"UPDATE knowledge_points SET {', '.join(assignments)} WHERE kp_id=?",
        (value, entity_id),
    )
    if cursor.rowcount == 0:
        raise KeyError(entity_id)


def _apply_one(pool, repo, item):
    status = item["status"]
    if status in {"noop", "invalid", "conflict"}:
        return item
    entity_type = item["entity_type"]
    entity_id = item["entity_id"]
    state = _state(pool, entity_type, entity_id)
    if state is None:
        return _result(entity_type, entity_id, "invalid", "mirror state disappeared")
    path = Path(item["path"]) if item.get("path") else entity_path(
        repo, pool.course, entity_type, entity_id
    )
    if status == "pool_to_repo":
        authored = pool_projection(pool, entity_type, entity_id)
        revision = state["revision"] + 1
        _atomic_write(path, _envelope(entity_type, entity_id, revision, authored))
        _put_state(pool, entity_type, entity_id, revision, authored, status)
        return _result(
            entity_type, entity_id, "exported", revision=revision, path=path,
        )
    if status == "restore_repo_file":
        authored = pool_projection(pool, entity_type, entity_id)
        revision = state["revision"] + 1
        _put_state(pool, entity_type, entity_id, revision, authored, status)
        _atomic_write(path, _envelope(entity_type, entity_id, revision, authored))
        return _result(
            entity_type, entity_id, "restored", revision=revision, path=path,
        )
    if status == "recover_converged":
        envelope = read_entity(path, pool.course, entity_type)
        pool_now = pool_projection(pool, entity_type, entity_id)
        baseline, incoming, _upgrade, error = _align_projection(
            state["content"], pool_now, envelope["content"]
        )
        if error:
            raise MirrorError(error)
        authored, error = _normalise_incoming(
            pool, entity_type, entity_id, baseline, incoming,
        )
        if error:
            raise MirrorError(error)
        with pool.transaction(immediate=True):
            _atomic_write(path, _envelope(entity_type, entity_id, envelope["revision"], authored))
            _put_state(pool, entity_type, entity_id, envelope["revision"], authored, status)
        return _result(
            entity_type, entity_id, "recovered",
            revision=envelope["revision"], path=path,
        )
    if status == "repo_to_pool":
        envelope = read_entity(path, pool.course, entity_type)
        pool_now = pool_projection(pool, entity_type, entity_id)
        baseline, incoming, _upgrade, error = _align_projection(
            state["content"], pool_now, envelope["content"]
        )
        if error:
            raise MirrorError(error)
        authored, error = _normalise_incoming(
            pool, entity_type, entity_id, baseline, incoming,
        )
        if error:
            raise MirrorError(error)
        patch = {key: authored[key] for key in authored if authored[key] != baseline[key]}
        with pool.transaction(immediate=True):
            if entity_type == "problem":
                _apply_problem_patch(pool, entity_id, patch, authored)
            elif entity_type == "kp":
                _apply_kp_patch(pool, entity_id, patch)
            else:
                content.update(pool, entity_type, entity_id, patch)
            actual = pool_projection(pool, entity_type, entity_id)
            if actual != authored:
                raise MirrorError(
                    f"governed mutation did not produce the requested projection for {entity_id}"
                )
            _atomic_write(path, _envelope(entity_type, entity_id, envelope["revision"], actual))
            _put_state(pool, entity_type, entity_id, envelope["revision"], actual, status)
        return _result(
            entity_type, entity_id, "applied", revision=envelope["revision"], path=path
        )
    raise MirrorError(f"cannot apply mirror status: {status}")


def sync(pool, repo, entity_id=None, dry_run=False):
    report = plan(pool, repo, entity_id)
    if dry_run:
        report["dry_run"] = True
        return report
    output = []
    for item in report["items"]:
        if "entity_type" not in item:
            output.append(item)
            continue
        try:
            output.append(_apply_one(pool, Path(repo).resolve(), item))
        except (MirrorError, ValueError, KeyError, sqlite3.Error, OSError) as exc:
            output.append(_result(
                item["entity_type"], item["entity_id"], "invalid", str(exc),
                path=item.get("path"),
            ))
    return _report(output, report["delete_requests"])


def check(pool, repo, entity_id=None):
    """Read-only validation plus the same semantic classification used by sync."""
    return plan(pool, repo, entity_id)


def _report(items, deletion_requests):
    counts = {}
    for item in items:
        status = item.get("status", "invalid")
        counts[status] = counts.get(status, 0) + 1
    return {
        "items": items,
        "counts": counts,
        "delete_requests": deletion_requests,
        "valid": not any(
            item.get("status") in {"invalid", "conflict"} for item in items
        ) and not any(item.get("status") == "invalid" for item in deletion_requests),
    }
