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

from workbench.data import content


SCHEMA_VERSION = 1
ENTITY_DIRS = {
    "kp": "knowledge",
    "problem": "problems",
    "relation": "relations",
}
# The mirror follows the governed data CRUD surface, except file-backed figure
# attachment metadata. Figures have their own ingest/figure contract and will be
# added only through that authority rather than by turning a path string into a
# generic repository-editable field.
MIRROR_FIELDS = {
    entity_type: set(fields) for entity_type, fields in content.EDITABLE_FIELDS.items()
}
MIRROR_FIELDS["problem"].discard("figure_paths")
ARRAY_FIELDS = {
    "kp": {"related_kp_ids"},
    "problem": {"kp_ids", "practice_modes"},
}
OBJECT_FIELDS = {"problem": {"micro_quiz"}}
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
    return {
        field: row[field]
        for field in sorted(MIRROR_FIELDS[entity_type])
        if field in row
    }


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
    for entity_type, directory in ENTITY_DIRS.items():
        folder = _course_root(repo, course) / directory
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*.json")):
            try:
                envelope = read_entity(path, course, entity_type)
                key = (entity_type, envelope["entity_id"])
                if key in found or key in ambiguous:
                    # Identity is inside JSON, not in the path. Two or more files
                    # that claim one identity are ambiguous, so none may win by
                    # scan order — including a third or later duplicate.
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
    return found, errors


def _read_delete_requests(repo, course):
    folder = Path(repo).resolve() / "delete-requests"
    items = []
    if not folder.exists():
        return items
    for path in sorted(folder.glob("*.json")):
        try:
            value = _load_json(path)
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


def init(pool, repo, entity_id=None, dry_run=False):
    """Pool-first bootstrap. Existing matching files are adopted; conflicts are refused."""
    _require_tables(pool)
    repo = Path(repo).resolve()
    found, parse_errors = _scan_repo(repo, pool.course)
    results = []
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
            if existing is None:
                _atomic_write(path, _envelope(entity_type, identity, 1, authored))
            _put_state(pool, entity_type, identity, 1, authored, "init")
        results.append(_result(
            entity_type, identity, "initialized", revision=1,
            path=existing_path if existing is not None else path,
        ))
    if entity_id and not any(item["entity_id"] == entity_id for item in results):
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
    if repo_entry is None:
        return _result(entity_type, entity_id, "restore_repo_file", revision=revision + 1)

    path, envelope = repo_entry
    if envelope["entity_id"] != entity_id:
        return _result(entity_type, entity_id, "invalid", "entity identity mismatch", path=path)
    if set(envelope["content"]) != set(baseline):
        return _result(
            entity_type, entity_id, "invalid",
            "content fields must match the initialized authored projection exactly",
            revision, path=path,
        )
    repo_now, error = _normalise_incoming(
        pool, entity_type, entity_id, baseline, envelope["content"],
    )
    if error:
        return _result(entity_type, entity_id, "invalid", error, revision, path=path)
    repo_revision = envelope["revision"]
    pool_changed = pool_now != baseline
    repo_changed = repo_now != baseline
    if not repo_changed:
        if repo_revision != revision:
            return _result(
                entity_type, entity_id, "invalid",
                f"unchanged content must keep revision {revision}", revision, path=path,
            )
        if pool_changed:
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


def _normalise_incoming(pool, entity_type, entity_id, baseline, incoming):
    patch = {key: incoming[key] for key in incoming if incoming[key] != baseline[key]}
    if not patch:
        return incoming, None
    if entity_type == "problem":
        plan = content.plan_problem_update(pool, entity_id, patch)
        if plan["errors"]:
            return incoming, "; ".join(plan["errors"])
        return {**baseline, **plan["fields"]}, None
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
            # An unreadable/ambiguous file has no trustworthy identity. It may
            # be a renamed copy of this tracked entity, so treating absence as a
            # safe deletion-and-restore would risk overwriting authored work.
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
        authored, error = _normalise_incoming(
            pool, entity_type, entity_id, state["content"], envelope["content"],
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
        baseline = state["content"]
        incoming = envelope["content"]
        authored, error = _normalise_incoming(
            pool, entity_type, entity_id, baseline, incoming,
        )
        if error:
            raise MirrorError(error)
        patch = {key: authored[key] for key in authored if authored[key] != baseline[key]}
        with pool.transaction(immediate=True):
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
