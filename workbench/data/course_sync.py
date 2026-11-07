"""File exchange projections of committed course data, without Git transport."""

import base64
import json
import os
import re
import sqlite3
import tempfile
from contextlib import contextmanager
from collections import ChainMap
from pathlib import Path, PurePosixPath
from uuid import uuid4

from workbench.data.pool import ensure_course_sync_schema
from workbench.data.course_sync_lock import exclusive

from workbench import registry
from workbench.data import content as content_data
from workbench.data import course_bundle
from workbench.data import figure_mirror
from workbench.data import paper_progress
from workbench.domain import course_sync as planning
from workbench.domain import course_sync_references as references


FORMAT_VERSION = 1
#: Plain copies of managed files inside the package, the Tutor-readable view.
READABLE_DIR = "files"
#: Retired ingest-candidate staging tables: known so a legacy pool exports, never carried.
RETIRED_TABLES = {"candidate_problems", "candidate_attempts"}
#: Columns the owning contracts deleted; a legacy row keeps the value in its own pool,
#: never in the exchange (DATA_MODEL "已删除字段").
RETIRED_COLUMNS = {"problems": frozenset({"topic_label"})}
TABLES = {
    "knowledge_points", "knowledge_relations", "problems", "flash_cards",
    "questions", "question_progress", "kp_progress", "problem_progress",
    "problem_attempts", "feedback_events", "review_schedule", "learner_signals",
    "learning_current_state", "kp_experiences", "kp_experience_problems",
    "active_practice", "active_practice_items", "paper_state", "practice_runs",
    "problem_revisions", "practice_execution_ids", "attempt_operations",
    "practice_request_operations", "part_attempt_context", "part_grading_revisions",
    "part_grading_jobs", "content_mirror_state", "content_mirror_log",
    "content_sequences", "ingest_batches", "candidate_problems", "candidate_attempts",
    "retired_paper_items",
}
IDENTITY_TABLES = {"problem_attempts", "feedback_events", "practice_runs",
                   "practice_execution_ids", "content_mirror_log", "question_progress"}
#: Append-only per-Paper history whose natural key (paper, local sequence) repeats on
#: two machines. Its identity therefore carries the installation origin, and a
#: received row takes the next local sequence instead of the sender's number.
HISTORY_TABLES = {"retired_paper_items"}
#: References a historical snapshot may hold without making the package unexportable.
DANGLING_TOLERANT = {"retired_paper_items": {"attempt_id"}}
INTEGER_REFERENCES = {"attempt_id": "problem_attempts", "execution_id": "practice_execution_ids"}
REFERENCE_JSON_FIELDS = {
    "practice_runs": {"items_json"},
    "paper_state": {"checkpoint_json"},
    "attempt_operations": {"result", "pre_state", "post_state"},
    "practice_request_operations": {"payload", "result"},
    "part_grading_revisions": {"request_json", "payload_json"},
}
WINDOWS_DEVICE_NAMES = {"con", "prn", "aux", "nul"} | {
    prefix + str(number) for prefix in ("com", "lpt") for number in range(1, 10)}


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc


def _atomic_json(path, value, *, indent=2):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=indent) + "\n")
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


#: Resolving a root costs a filesystem round trip per call on Windows, and every
#: managed path in one exchange shares the same root. The mapping is read-only:
#: the escape and symlink checks below still run for every path.
_RESOLVED_ROOTS = {}


def _resolved_root(root):
    key = str(root)
    cached = _RESOLVED_ROOTS.get(key)
    if cached is None:
        cached = _RESOLVED_ROOTS[key] = Path(root).resolve()
    return cached


def _relative(root, value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    parts = PurePosixPath(value)
    if parts.is_absolute() or any(part.lower().rstrip(" .") in {"", "..", ".git"}
                                 or part != part.rstrip(" .")
                                 or part.split(".", 1)[0].lower() in WINDOWS_DEVICE_NAMES
                                 for part in parts.parts):
        raise ValueError(f"unsafe relative path: {value!r}")
    if value in {".", "./"}:
        raise ValueError("path must identify a managed file or directory")
    root = _resolved_root(root)
    target = root / parts
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"path escapes its root: {value!r}")
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink is not a managed exchange path: {value!r}")
    return target


@contextmanager
def course_lock(root):
    """Serialize exchange writers with ownership released by the operating system."""
    with exclusive(Path(root) / ".lessonkit/course-sync/write.lock"):
        yield


def _installation_origin(*, read_only=False):
    path = registry.base_dir() / "course-sync-installation.json"
    if read_only and not path.exists():
        return "unassigned-local"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with exclusive(path.with_suffix(".lock")):
            if not path.exists():
                _atomic_json(path, {"origin": "installation-" + str(uuid4())})
    value = _read_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("origin"), str) or not value["origin"]:
        raise ValueError("invalid installation origin")
    return value["origin"]


def _state(root, course, *, read_only=False, pool=None):
    path = Path(root) / ".lessonkit/course-sync/state.json"
    checkpoint = None
    if pool is not None and _table_exists(pool.connect(), "course_sync_checkpoint"):
        checkpoint = pool.connect().execute(
            "SELECT state_json FROM course_sync_checkpoint WHERE singleton=1").fetchone()
    if checkpoint is not None or path.exists():
        state = json.loads(checkpoint[0]) if checkpoint is not None else _read_json(path)
        if not isinstance(state, dict) or not isinstance(state.get("course"), dict) \
                or state["course"].get("id") != course:
            raise ValueError("course exchange state has a different course identity")
        if not isinstance(state.get("row_identities"), dict) or not isinstance(state.get("base"), dict):
            raise ValueError("invalid course exchange identity mappings or base")
        if pool is not None and _table_exists(pool.connect(), "course_sync_units"):
            pending = []
            for unit in pool.connect().execute("SELECT * FROM course_sync_units ORDER BY identity"):
                state["base"][unit["identity"]] = json.loads(unit["asset_json"])
                state["row_identities"].update(json.loads(unit["mappings_json"]))
                if unit["pending_json"]:
                    pending.append(json.loads(unit["pending_json"]))
            if pending:
                state["pending_files"] = pending
        state["origin"] = _installation_origin(read_only=read_only)
        return state
    return {"course": {"id": course, "origin": None if read_only else "course-" + str(uuid4())},
            "origin": _installation_origin(read_only=read_only), "row_identities": {}, "base": {},
            "initialized": False}


def _checkpoint(connection, state):
    ensure_course_sync_schema(connection)
    snapshot = {key: value for key, value in state.items() if key != "pending_files"}
    connection.execute(
        "INSERT INTO course_sync_checkpoint(singleton,state_json) VALUES(1,?) "
        "ON CONFLICT(singleton) DO UPDATE SET state_json=excluded.state_json",
        (json.dumps(snapshot, ensure_ascii=False),))
    connection.execute("DELETE FROM course_sync_units WHERE pending_json IS NULL")


def _unit_checkpoint(connection, acknowledged, mappings, pending=None):
    for identity, asset in acknowledged.items():
        intent = pending if pending and pending["identity"] == identity else None
        connection.execute(
            "INSERT INTO course_sync_units(identity,asset_json,mappings_json,pending_json) "
            "VALUES(?,?,?,?) ON CONFLICT(identity) DO UPDATE SET "
            "asset_json=excluded.asset_json,mappings_json=excluded.mappings_json,"
            "pending_json=excluded.pending_json",
            (identity, json.dumps(asset, ensure_ascii=False),
             json.dumps(mappings, ensure_ascii=False),
             json.dumps(intent, ensure_ascii=False) if intent else None))


def _save_state(pool, state):
    with pool.transaction(immediate=True):
        _checkpoint(pool.connect(), state)
    _atomic_json(pool.root / ".lessonkit/course-sync/state.json", state)


def _complete_pending_files(pool, state, identities=None):
    failed, remaining, published = [], [], []
    for change in state.get("pending_files", []):
        identity = change["identity"]
        if identities is not None and identity not in identities:
            remaining.append(change)
            continue
        try:
            _file_payload(pool.root, change, db_path=pool.db_path)
            _write_file(pool.root, change)
        except (OSError, ValueError) as exc:
            remaining.append(change)
            failed.append({"identity": identity, "code": "publication_pending", "message": str(exc)})
            continue
        published.append((identity,))
    # A crash before this commit replays the same atomic replacements/deletions.
    if published:
        with pool.transaction(immediate=True):
            pool.connect().executemany("UPDATE course_sync_units SET pending_json=NULL WHERE identity=?", published)
    if remaining:
        state["pending_files"] = remaining
    else:
        state.pop("pending_files", None)
    return failed


def _database_projection(pool, state):
    connection = pool.connect()
    if connection.in_transaction:
        raise ValueError("save or finish the current database transaction before exporting")
    snapshot = sqlite3.connect(":memory:")
    snapshot.row_factory = sqlite3.Row
    connection.backup(snapshot)
    try:
        names = {row[0] for row in snapshot.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        names.difference_update({"course_sync_checkpoint", "course_sync_units"})
        unknown = names - TABLES
        if unknown:
            raise ValueError("unregistered course tables: " + ", ".join(sorted(unknown)))
        # Legacy pools still carry the retired ingest-candidate staging tables.
        # FILE_CONTRACT declares them out of the model, so they are skipped rather
        # than exported into a schema that no longer has them; the inventory says so.
        skipped = sorted(names & RETIRED_TABLES)
        names = names - RETIRED_TABLES
        if "paper_state" in names:
            pending = snapshot.execute("SELECT paper_id FROM paper_state "
                                       "WHERE pending_json IS NOT NULL OR pending_delete=1").fetchall()
            if pending:
                raise ValueError("finish saving pending Paper files before exporting")
        assets, inventory = {}, []
        for table in sorted(names):
            columns = list(snapshot.execute(f'PRAGMA table_info("{table}")'))
            keys = [row["name"] for row in sorted(columns, key=lambda row: row["pk"]) if row["pk"]]
            if not keys:
                raise ValueError(f"course table has no persistent key: {table}")
            rows = snapshot.execute(f'SELECT * FROM "{table}" ORDER BY '
                                    + ",".join(f'"{key}"' for key in keys)).fetchall()
            dropped = RETIRED_COLUMNS.get(table, frozenset())
            if dropped:
                columns = [row for row in columns if row["name"] not in dropped]
            inventory.append({"table": table, "columns": [row["name"] for row in columns],
                              "primary_key": keys, "rows": len(rows),
                              "retired_columns": sorted(dropped)})
            for source in rows:
                row = {name: value for name, value in dict(source).items() if name not in dropped}
                key = [row[name] for name in keys]
                spelling = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
                local_key = table + "/" + spelling
                identities = state["row_identities"]
                if local_key not in identities:
                    prefix = (state["origin"] + "/"
                              if table in IDENTITY_TABLES or table in HISTORY_TABLES else "")
                    identities[local_key] = "row/" + table + "/" + prefix + spelling
                identity = identities[local_key]
                assets[identity] = {"kind": "row", "content": {"table": table, "key": keys, "row": row},
                                    "depends_on": []}
                if table == "problems" and row.get("deleted_at"):
                    assets[identity]["deleted"] = True
        dangling = _portable_integer_references(assets, state)
        if dangling:
            inventory.append({"table": "", "columns": [], "primary_key": [], "rows": 0,
                              "dangling_history_references": dangling})
        if skipped:
            inventory.append({"table": "", "columns": [], "primary_key": [],
                              "rows": 0, "retired_tables": skipped})
        return assets, inventory
    finally:
        snapshot.close()


def _portable_integer_references(assets, state):
    records = {}
    for identity, asset in assets.items():
        content = asset["content"]
        if content["table"] in IDENTITY_TABLES:
            records[(content["table"], content["row"]["id"])] = identity

    dangling = []

    def reference(table, value):
        if value is None:
            return None
        if type(value) is not int or (table, value) not in records:
            raise ValueError(f"unresolved course record reference: {table}/{value}")
        identity = records[(table, value)]
        dependencies.add(identity)
        return identity

    def tolerant_reference(table, value, field):
        """A historical snapshot keeps its row even when the referenced fact is gone."""
        try:
            return reference(table, value)
        except ValueError:
            dangling.append({"table": table, "field": field, "value": value})
            return None

    for identity, asset in list(assets.items()):
        dependencies = set()
        content = asset["content"]
        table, row = content["table"], content["row"]
        local_key = table + "/" + json.dumps([row[key] for key in content["key"]],
                                            ensure_ascii=False, separators=(",", ":"))
        if table in IDENTITY_TABLES:
            row["id"] = identity
        tolerant = DANGLING_TOLERANT.get(table, frozenset())
        for field, target in INTEGER_REFERENCES.items():
            if field not in row:
                continue
            if field in tolerant:
                row[field] = tolerant_reference(target, row[field], field)
            else:
                row[field] = reference(target, row[field])
        for field in REFERENCE_JSON_FIELDS.get(table, ()):
            if not row.get(field):
                continue
            value = json.loads(row[field])
            converted = references.convert_json(table, field, value, reference)
            if converted != value:
                row[field] = references.serialize_json(table, field, converted)
        if any(key in INTEGER_REFERENCES for key in content["key"]):
            portable_key = json.dumps([row[key] for key in content["key"]],
                                      ensure_ascii=False, separators=(",", ":"))
            replacement = "row/" + table + "/" + portable_key
            del assets[identity]
            assets[replacement] = asset
            state["row_identities"][local_key] = replacement
            identity = replacement
        asset["depends_on"] = sorted(dependencies - {identity})
    return dangling


def _managed_files(pool, assets, pending=None, tracked=None):
    pending = pending or {}
    tracked = tracked or {}
    root = pool.root
    files = set()
    for name in ("goals.json", "course-preferences.json"):
        path = root / ".lessonkit" / name
        if path.exists() and path.relative_to(root).as_posix() not in pending:
            value = _read_json(path)
            if name == "goals.json" and (not isinstance(value, list)
                                         or not all(isinstance(item, dict) for item in value)):
                raise ValueError("goals.json must contain a list of objects")
            files.add(path)
    for folder in (root / ".lessonkit/practice-sets", root / ".lessonkit/learning"):
        if folder.exists():
            files.update(path for path in folder.rglob("*") if path.is_file())
    # Reuse the existing declared logical figure references and layout resolution.
    references = set()
    for asset in assets.values():
        content = asset["content"]
        if content["table"] in {"knowledge_points", "problems"}:
            row = content["row"]
            references.update(figure_mirror._decode_paths(row.get("figure_paths"), content["table"]))
    for logical in sorted(references):
        figure_mirror.validate_references(pool.course, [logical], logical)
        source, _layout = figure_mirror._workspace_source(pool, logical)
        if source is None:
            if ".lessonkit/figures/" + logical in pending:
                continue
            raise ValueError(f"missing referenced figure: {logical}")
        files.add(source)
    config_path = root / ".lessonkit/course-sync/config.json"
    if config_path.exists():
        config = _read_json(config_path)
        paths = config.get("managed_paths", []) if isinstance(config, dict) else None
        if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
            raise ValueError("managed_paths must be a list of relative paths")
        for name in paths:
            path = _relative(root, name)
            if not path.exists():
                if name in pending:
                    continue
                raise ValueError(f"missing managed course path: {name}")
            if path.is_dir():
                files.update(item for item in path.rglob("*") if item.is_file())
            else:
                files.add(path)
    for asset in tracked.values():
        if asset.get("kind") != "file" or not asset.get("content"):
            continue
        target = _relative(root, asset["content"].get("path"))
        if target.is_file():
            files.add(target)
        elif target.exists():
            raise ValueError(f"managed course file is not a regular file: {target.relative_to(root)}")
    for path in sorted(files):
        relative = path.relative_to(root).as_posix()
        _relative(root, relative)
        if path == pool.db_path or path.name in {".env", ".credentials.yaml"} or any(
                part in {"jobs", ".git", "course-sync"} for part in path.relative_to(root).parts):
            raise ValueError(f"path is not a portable course asset: {relative}")
        yield relative, path


def _projection(pool, state):
    assets, inventory = _database_projection(pool, state)
    pending = {change["asset"]["content"]["path"]: change
               for change in state.get("pending_files", [])}
    for relative, path in _managed_files(pool, assets, pending, state["base"]):
        assets["file/" + relative] = {
            "kind": "file", "content": {"path": relative, "encoding": "base64",
                                         "data": base64.b64encode(path.read_bytes()).decode("ascii")},
            "depends_on": []}
    for relative, change in pending.items():
        assets["file/" + relative] = change["asset"]
    _execution_projection(assets, state)
    for identity, asset in state["base"].items():
        if identity not in assets and asset.get("deleted"):
            assets[identity] = asset
    return assets, inventory


def _execution_projection(assets, state):
    active = None
    active_items = []
    checkpoints = []
    generations = {}
    for identity, asset in list(assets.items()):
        if asset["kind"] != "row":
            continue
        content = asset["content"]
        table, row = content["table"], content["row"]
        if table == "active_practice":
            active = dict(row)
            del assets[identity]
        elif table == "active_practice_items":
            active_items.append(dict(row))
            del assets[identity]
        elif table == "paper_state":
            generations[row["paper_id"]] = row["generation"]
            if row.get("checkpoint_json"):
                checkpoints.append(json.loads(row["checkpoint_json"]))
                row["checkpoint_json"] = None
                asset["depends_on"] = []
    if active is not None:
        active.pop("singleton", None)
        active["kp_ids"] = json.loads(active.pop("kp_ids_json") or "[]")
        active["items"] = sorted(active_items, key=lambda item: item["position"])
        checkpoints.append(active)
    elif active_items:
        raise ValueError("active practice items have no execution header")
    for record in checkpoints:
        header = dict(record)
        items = header.pop("items")
        execution_id = header["execution_id"]
        identity = "execution/" + execution_id
        if identity in assets:
            raise ValueError("execution is both selected and parked")
        metadata = {key: header.pop(key) for key in ("cursor", "updated_at", "progress") if key in header}
        metadata["selected"] = record is active
        paper_id = header.get("source_ref")
        header["paper_id"] = paper_id
        # The header owns the item set: a receiver must drop a local item the
        # sender no longer has, and position alone cannot say whether it moved.
        header["items"] = [{"position": item.get("position"),
                            "item_type": item.get("item_type"),
                            "item_id": item.get("item_id"),
                            "direction": item.get("direction") or ""} for item in items]
        dependencies = [execution_id]
        if paper_id:
            dependencies.append("file/.lessonkit/practice-sets/" + paper_id + ".json")
        assets[identity] = {"kind": "execution", "content": header,
                            "depends_on": dependencies, "presentation": metadata}
        for raw in items:
            item = dict(raw)
            item.pop("locked", None)
            if "draft_json" in item:
                item["draft"] = json.loads(item.pop("draft_json") or "{}")
            sequence = item.pop("draft_sequence", 0)
            item.update(execution_id=execution_id, paper_id=paper_id,
                        paper_generation=header["paper_generation"])
            item_dependencies = [identity]
            if item.get("attempt_id"):
                item_dependencies.append(item["attempt_id"])
            def draft_reference(table, value):
                if type(value) is int:
                    key = table + "/" + json.dumps([value], separators=(",", ":"))
                    value = state["row_identities"].get(key)
                if not isinstance(value, str) or value not in assets:
                    raise ValueError("unresolved part draft attempt reference")
                item_dependencies.append(value)
                return value
            if "draft" in item:
                item["draft"] = references.convert_draft(item["draft"], draft_reference)
            key = identity + "/item/" + str(item["position"])
            if key in assets:
                raise ValueError("duplicate execution item position")
            assets[key] = {"kind": "execution_item", "content": item,
                           "depends_on": item_dependencies, "presentation": {"draft_sequence": sequence}}
    for identity, old in state["base"].items():
        if identity in assets or old.get("kind") not in {"execution", "execution_item"}:
            continue
        content = old["content"]
        generation = generations.get(content.get("paper_id"))
        if generation is not None and generation > content.get("paper_generation", 0):
            assets[identity] = {**old, "deleted": True}


def export_course(pool, workspace, destination):
    """Export a closed committed projection, rejecting unknown or missing assets."""
    destination = Path(destination).resolve()
    with course_lock(pool.root):
        state = _state(pool.root, pool.course, pool=pool)
        publication_errors = _complete_pending_files(pool, state)
        assets, inventory = _projection(pool, state)
        missing = sorted(identity for identity, asset in state["base"].items()
                         if identity not in assets and not asset.get("deleted"))
        if missing:
            raise ValueError("managed assets are missing without explicit deletion: " + ", ".join(missing))
        # Establish the initial shared image once. Merely exporting subsequent
        # edits is not evidence that another installation has received them.
        if not state.get("initialized", True):
            state["base"] = assets
            state["initialized"] = True
        previous_assets, previous_paths = {}, {}
        previous_manifest = None
        if (destination / "manifest.json").exists():
            previous = read_exchange(destination)
            previous_manifest = _read_json(destination / "manifest.json")
            if previous["course"] != state["course"]:
                raise ValueError("destination package belongs to a different course origin")
            previous_assets = previous["assets"]
            previous_paths = {item["identity"]: item["path"]
                              for item in previous_manifest["assets"]}
        # Persist source identities before publishing anything another device can
        # receive. A failed first export must retain the same course lineage.
        _save_state(pool, state)
        # An unchanged projection keeps its export generation, so a repeated
        # export of the same content does not manufacture a new commit.
        version = (course_bundle.FORMAT_VERSION_INDIVIDUAL
                   if len(assets) <= course_bundle.INDIVIDUAL_LIMIT
                   else course_bundle.FORMAT_VERSION_GROUPED)
        new_generation = previous_assets != assets or (previous_manifest or {}).get("format_version") != version
        export_id = ("export-" + str(uuid4()) if new_generation
                     else previous_manifest["export_id"])
        layout = course_bundle.pack(assets, export_id, previous_manifest, previous_assets)
        for relative, value in layout["files"].items():
            _atomic_json(_relative(destination, relative), value,
                         indent=None if version == course_bundle.FORMAT_VERSION_GROUPED else 2)
        descriptors, written = layout["descriptors"], layout["written"]
        manifest = {"format_version": version, "course": state["course"],
                    "origin": state["origin"], "export_id": export_id,
                    "assets": descriptors, "base": state["base"], "tables": inventory}
        changed = previous_manifest != manifest
        if changed:
            _atomic_json(destination / "manifest.json", manifest)
        mirror_errors = _write_readable_files(destination, assets)
        cleanup_errors = list(mirror_errors) + publication_errors
        live_paths = {item["path"] for item in descriptors}
        for relative in sorted(set(previous_paths.values()) - live_paths):
            path = _relative(destination, relative)
            try:
                path.unlink(missing_ok=True)
                parent = path.parent
                while parent != destination:
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
            except OSError as exc:
                cleanup_errors.append({"path": relative, "message": str(exc)})
        state["last_export"] = {"id": export_id, "assets": assets}
        _save_state(pool, state)
        return {"status": "partial" if cleanup_errors else "success",
                "course": state["course"], "origin": state["origin"],
                "export_id": export_id, "assets": len(assets), "tables": inventory,
                "written": written, "reused": len(assets) - written,
                "manifest_changed": changed, "cleanup_errors": cleanup_errors,
                "destination": str(destination), "local": {"exported": True}, "remote": None}


def _write_readable_files(destination, assets):
    """Keep a plain copy of every managed file so a Tutor can read and edit it.

    The envelopes stay the exchange truth; this mirror is the human/Tutor
    surface, and a reception prefers its bytes when they were edited
    (`apply_exchange`). Stale copies from an earlier export are removed.
    """
    folder = Path(destination) / READABLE_DIR
    wanted = {asset["content"]["path"]: asset for asset in assets.values()
              if asset["kind"] == "file" and not asset.get("deleted")}
    written, errors = set(), []
    for relative, asset in sorted(wanted.items()):
        try:
            target = _relative(folder, relative)
            data = base64.b64decode(asset["content"]["data"], validate=True)
            if not target.is_file() or target.read_bytes() != data:
                _atomic_bytes(target, data)
            written.add(relative)
        except (ValueError, OSError) as exc:
            errors.append({"path": relative, "message": str(exc)})
    previous = {path.relative_to(folder).as_posix()
                for path in folder.rglob("*") if path.is_file()} if folder.is_dir() else set()
    stale = previous - written
    for relative in sorted(stale):
        try:
            _relative(folder, relative).unlink(missing_ok=True)
        except (ValueError, OSError) as exc:
            errors.append({"path": relative, "message": str(exc)})
    return errors


def _database_guard(pool):
    connection = pool.connect()
    return [id(connection), connection.execute("PRAGMA data_version").fetchone()[0],
            connection.total_changes]


class StaleInspection(ValueError):
    """The course changed after inspection, so no later unit can be applied."""


def _check_database_guard(pool, expected):
    if expected is not None and _database_guard(pool) != expected:
        raise StaleInspection("course changed after inspection; inspect again before applying")


def inspect_exchange(pool, workspace, source):
    """Inspect a package and target schema without writing course/registry state."""
    if not pool.db_path.is_file():
        raise ValueError("target course database does not exist")
    database_guard = _database_guard(pool)
    package = read_exchange(source)
    if package["course"]["id"] != pool.course:
        raise ValueError("exchange package belongs to a different course")
    state = _state(pool.root, pool.course, read_only=True, pool=pool)
    local, inventory = _projection(pool, state)
    errors = list(package["errors"])
    errors.extend({"identity": item["identity"], "code": "publication_pending",
                   "message": "a committed local file still needs publication"}
                  for item in state.get("pending_files", []))
    schema = {item["table"]: item for item in inventory}
    incoming = dict(package["assets"])
    for identity, asset in list(incoming.items()):
        if asset["kind"] != "row" or not asset.get("content"):
            continue
        content = asset["content"]
        table = schema.get(content["table"]) or _declared_history_table(content["table"])
        if table is None or content["key"] != table["primary_key"] \
                or not set(content["row"]) <= set(table["columns"]) \
                or not set(content["key"]) <= set(content["row"]) \
                or any(type(value) not in {str, int, float, type(None)}
                       for value in content["row"].values()):
            errors.append({"identity": identity, "code": "invalid_asset",
                           "message": "row does not match the target course schema"})
            del incoming[identity]
    invalid_headers = {error["identity"].rsplit("/item/", 1)[0] for error in errors
                       if isinstance(error.get("identity"), str)
                       and error["identity"].startswith("execution/") and "/item/" in error["identity"]}
    for identity in sorted(invalid_headers):
        if identity in incoming:
            del incoming[identity]
            errors.append({"identity": identity, "code": "invalid_dependency",
                           "message": "the execution contains an invalid item"})
    base = _common_base(state, local, package, errors)
    plan = planning.plan_exchange(base, local, incoming)
    errors.extend(plan["errors"])
    association_required = bool(local) and state["course"]["origin"] != package["course"]["origin"]
    return {"course": package["course"], "local": local, "incoming": incoming,
            "database_guard": database_guard,
            "row_identities": dict(state["row_identities"]),
            "source": str(Path(source).resolve()),
            "base": base, "tables": inventory, "errors": errors, "plan": plan,
            "changes": plan["changes"], "outgoing": plan["outgoing"],
            "conflicts": plan["conflicts"], "unchanged": plan["unchanged"],
            "association_required": association_required,
            "export_id": package.get("export_id")}


def _declared_history_table(table):
    """A history table this receiver owns but has not migrated into the pool yet."""
    if table not in HISTORY_TABLES or table != "retired_paper_items":
        return None
    from workbench.data.pool import RETIRED_PAPER_ITEM_COLUMNS, RETIRED_PAPER_ITEM_KEYS
    return {"table": table, "columns": list(RETIRED_PAPER_ITEM_COLUMNS),
            "primary_key": list(RETIRED_PAPER_ITEM_KEYS), "rows": 0}


def _common_base(state, local, package, errors):
    """The projection this installation has acknowledged, cross-checked against
    the sender's claim.

    Export never advances the base; only a completed reception acknowledges an
    asset, so a repeated export cannot speak for the other installation. The
    sender's base is used as an extra witness: an asset it calls shared that we
    hold with different content was never acknowledged on this side, which
    makes a later comparison ambiguous and is reported instead of guessed.
    """
    base = dict(state["base"])
    for identity, ancestor in package["base"].items():
        if identity in base or identity not in local:
            continue
        if _same_projection(local[identity], ancestor):
            base[identity] = ancestor
            continue
        errors.append({"identity": identity, "code": "baseline_mismatch",
                       "message": "the package calls this asset shared but this "
                                  "installation never acknowledged it"})
        base[identity] = ancestor
    return base


def _same_projection(left, right):
    def semantic(asset):
        return {"kind": asset.get("kind"), "content": asset.get("content"),
                "depends_on": sorted(set(asset.get("depends_on") or [])),
                "deleted": bool(asset.get("deleted"))}
    try:
        return semantic(left) == semantic(right)
    except AttributeError:
        return False


def _adopt_course_origin(state, inspection, choices):
    """Keep the lineage of a received course; a different lineage needs input."""
    package = inspection.get("course") or {}
    origin = package.get("origin")
    if not isinstance(origin, str) or not origin:
        return
    if not inspection.get("local"):
        # Nothing recorded a lineage here yet, so the package supplies it.
        state["course"]["origin"] = origin
        return
    if state["course"]["origin"] != origin and not choices.get("associate"):
        raise ValueError("the package belongs to a different course lineage; "
                         "explicit association input is required")
    state["course"]["origin"] = origin


def _side_choices(plan, choices):
    """Split conflicts into incoming changes and kept-local units."""
    choices = choices or {}
    if not isinstance(choices, dict):
        raise ValueError("conflict choices must be an object")
    default = choices.get("side")
    items = choices.get("items") or {}
    if default not in {None, "local", "incoming"} or not isinstance(items, dict):
        raise ValueError("a conflict side is local or incoming")
    changes = list(plan.get("changes") or [])
    kept = []
    unresolved = []
    for conflict in plan.get("conflicts") or []:
        identity = conflict["identity"]
        side = items.get(identity, default)
        if side not in {None, "local", "incoming"}:
            raise ValueError(f"invalid side for conflict {identity!r}")
        if side == "incoming":
            action = "update" if conflict.get("local") else "create"
            changes.append({"identity": identity, "action": action,
                            "asset": conflict["incoming"]})
        elif side == "local":
            kept.append(identity)
        else:
            unresolved.append(conflict)
    return changes, kept, unresolved


def _dependency_order(changes):
    """Apply prerequisites first; an asset waiting on a blocked one is skipped."""
    pending = {item["identity"]: item for item in changes}
    ordered, blocked = [], set()
    while pending:
        progress = False
        for identity, item in sorted(pending.items()):
            depends = [key for key in item["asset"].get("depends_on", []) if key]
            if any(key in blocked for key in depends):
                blocked.add(identity)
                del pending[identity]
                progress = True
                continue
            if any(key in pending for key in depends):
                continue
            ordered.append(item)
            del pending[identity]
            progress = True
        if not progress:
            blocked.update(pending)
            break
    return ordered, blocked


def _identity_index(connection, state):
    """Persistent asset identity -> the local integer record holding it."""
    index = {}
    for table in sorted(IDENTITY_TABLES):
        if not _table_exists(connection, table):
            continue
        keys = _primary_key(connection, table)
        for row in connection.execute(f'SELECT * FROM "{table}"'):
            key = json.dumps([row[name] for name in keys],
                             ensure_ascii=False, separators=(",", ":"))
            identity = state["row_identities"].get(table + "/" + key)
            if identity:
                index[identity] = (table, row["id"])
    return index


def _table_exists(connection, table):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _primary_key(connection, table):
    columns = list(connection.execute(f'PRAGMA table_info("{table}")'))
    return [row["name"] for row in sorted(columns, key=lambda row: row["pk"]) if row["pk"]]


def _local_row(asset, index):
    """The projected row with its record references turned back into local ids."""
    content = asset["content"]
    table, row = content["table"], dict(content["row"])
    for field, target in INTEGER_REFERENCES.items():
        if row.get(field) is None:
            continue
        if row[field] not in index:
            raise ValueError(f"unresolved incoming reference: {row[field]}")
        row[field] = index[row[field]][1]
    for field in REFERENCE_JSON_FIELDS.get(table, ()):
        if not row.get(field):
            continue
        value = json.loads(row[field])
        converted = references.convert_json(table, field, value,
                                             lambda target, item: _local_identifier(item, index))
        if converted != value:
            row[field] = references.serialize_json(table, field, converted)
    return table, row


def _identity_key(identity):
    """The ordered key encoded by `row/<table>[/<origin>]/[<values>]`."""
    if not identity.startswith("row/"):
        return None
    marker = identity.find("[")
    if marker < 0:
        return None
    body = identity[len("row/"):marker]
    table = body.split("/", 1)[0]
    try:
        return table, json.loads(identity[marker:])
    except json.JSONDecodeError:
        return None


def apply_exchange(pool, workspace, inspection, choices=None):
    """Apply independent units with savepoints and bounded durable chunks."""
    if not isinstance(inspection, dict):
        raise ValueError("an inspection result is required")
    plan = inspection.get("plan") if isinstance(inspection.get("plan"), dict) else inspection
    if not isinstance(plan.get("changes"), list):
        raise ValueError("an exchange plan is required")
    if not pool.db_path.is_file():
        raise ValueError("target course database does not exist")
    choices = choices or {}
    changes, kept, unresolved = _side_choices(plan, choices)
    supported, unsupported = _supported_units(changes)
    with course_lock(pool.root):
        database_guard = list(inspection["database_guard"]) if inspection.get("database_guard") else None
        _check_database_guard(pool, database_guard)
        state_path = pool.root / ".lessonkit/course-sync/state.json"
        state = _state(pool.root, pool.course, pool=pool)
        _adopt_course_origin(state, inspection, choices)
        state["initialized"] = True
        unchanged = set(plan.get("unchanged") or [])
        state["row_identities"].update({key: identity for key, identity in
                                        inspection.get("row_identities", {}).items()
                                        if identity in unchanged})
        _save_state(pool, state)
        publication_errors = _complete_pending_files(pool, state)
        connection = pool.connect()
        if database_guard is not None:
            database_guard[2] = connection.total_changes
        index = _identity_index(connection, state)
        local_assets = inspection.get("local") or {}
        # A malformed execution envelope is a unit failure, not a crash after the
        # checkpoint row was written (C05 F4); a header waits for its items' own
        # dependencies, which grouping removed from the unit list (C05 F1a).
        malformed = [change for change in supported
                     if change["asset"]["kind"] in {"execution", "execution_item"}
                     and not _execution_unit_ready(change["asset"])]
        supported = [change for change in supported if change not in malformed]
        ordered, blocked = _dependency_order(_with_group_dependencies(supported))
        headers, executions = _execution_units(ordered, local_assets)
        invalid_headers = {change["identity"].rsplit("/item/", 1)[0] for change in supported
                           if change["identity"] in blocked and change["asset"]["kind"] == "execution_item"}
        blocked.update(invalid_headers)
        failed = [{"identity": identity, "code": "invalid_dependency",
                   "message": "the unit depends on an unavailable asset"}
                  for identity in sorted(blocked)]
        advisory = {"publication_pending"}
        if choices.get("associate"):
            # An explicit association accepts that the two sides never shared a
            # base; the planner still reports each content conflict on its own.
            advisory.add("baseline_mismatch")
        failed.extend(error for error in inspection.get("errors", [])
                      if error.get("code") not in advisory)
        failed.extend(publication_errors)
        failed.extend({"identity": identity, "code": "unsupported_kind",
                       "message": "this receiver cannot write that asset yet"}
                      for identity in sorted(unsupported))
        failed.extend({"identity": change["identity"], "code": "invalid_asset",
                       "message": "the execution envelope is incomplete"}
                      for change in malformed)
        applied = []
        failed_identities = {item["identity"] for item in failed}
        grouped_ack = {header: {} for header in headers}
        for item in ordered:
            if item["asset"]["kind"] == "execution_item":
                header = item["identity"].rsplit("/item/", 1)[0]
                if header in grouped_ack:
                    grouped_ack[header][item["identity"]] = item["asset"]
        independent = [item for item in ordered if not (
            item["asset"]["kind"] == "execution_item" and
            item["identity"].rsplit("/item/", 1)[0] in headers)]
        for chunk in _receive_chunks(independent):
            chunk_ack, chunk_mappings, chunk_index, chunk_pending = {}, {}, {}, []
            chunk_applied = []
            try:
                with pool.transaction(immediate=True):
                    _check_database_guard(pool, database_guard)
                    for change in chunk:
                        identity = change["identity"]
                        if identity in failed_identities:
                            continue
                        unavailable = [key for key in change["asset"].get("depends_on", [])
                                       if key in failed_identities]
                        if unavailable:
                            failed.append({"identity": identity, "code": "invalid_dependency",
                                           "message": f"a dependency did not apply: {unavailable[0]}"})
                            failed_identities.add(identity)
                            continue
                        mappings, index_delta = {}, {}
                        unit_state = {**state, "row_identities": ChainMap(mappings, chunk_mappings, state["row_identities"])}
                        unit_index = ChainMap(index_delta, chunk_index, index)
                        acknowledged = {identity: change["asset"], **grouped_ack.get(identity, {})}
                        pending = None
                        connection.execute("SAVEPOINT course_sync_unit")
                        try:
                            if identity in headers:
                                _write_execution(pool, connection, unit_state, unit_index, identity,
                                                 change["asset"], executions.get(identity, {}))
                            elif change["asset"]["kind"] == "execution_item":
                                _write_execution_item(connection, unit_index, identity, change["asset"])
                            elif change["asset"]["kind"] == "file":
                                _file_payload(pool.root, change, db_path=pool.db_path)
                                pending = change
                            else:
                                _write_unit(pool, connection, unit_state, unit_index, change)
                            _unit_checkpoint(connection, acknowledged, mappings, pending)
                        except Exception as exc:
                            connection.execute("ROLLBACK TO course_sync_unit")
                            connection.execute("RELEASE course_sync_unit")
                            failed.append({"identity": identity, "code": "apply_failed", "message": str(exc)})
                            failed_identities.add(identity)
                            continue
                        connection.execute("RELEASE course_sync_unit")
                        chunk_mappings.update(mappings)
                        chunk_index.update(index_delta)
                        chunk_ack.update(acknowledged)
                        if pending:
                            chunk_pending.append(pending)
                        chunk_applied.extend(acknowledged)
            except Exception as exc:
                connection.rollback()
                # No row, mapping, intent or acknowledgement in this chunk committed.
                for identity in chunk_applied:
                    failed.append({"identity": identity, "code": "apply_failed", "message": str(exc)})
                    failed_identities.add(identity)
                if not chunk_applied:
                    for change in chunk:
                        identity = change["identity"]
                        if identity not in failed_identities:
                            failed.append({"identity": identity, "code": "apply_failed", "message": str(exc)})
                            failed_identities.add(identity)
                if database_guard is not None:
                    database_guard[2] = connection.total_changes
                if isinstance(exc, StaleInspection):
                    # Every later chunk must fail the same re-check; report the
                    # remainder once instead of opening doomed transactions (C05 F3).
                    remaining = [item["identity"] for item in independent
                                 if item["identity"] not in failed_identities]
                    failed.append({"identity": "", "code": "stale_inspection",
                                   "message": f"{str(exc)}; {len(remaining)} units were not attempted"})
                    failed_identities.update(remaining)
                    break
                continue
            state["row_identities"].update(chunk_mappings)
            state["base"].update(chunk_ack)
            index.update(chunk_index)
            if chunk_pending:
                state.setdefault("pending_files", []).extend(chunk_pending)
                pending_errors = _complete_pending_files(pool, state, {item["identity"] for item in chunk_pending})
                failed.extend(pending_errors)
                failed_identities.update(item["identity"] for item in pending_errors)
            applied.extend(identity for identity in chunk_applied if identity not in failed_identities)
            if database_guard is not None:
                database_guard[2] = connection.total_changes
        for header, items in grouped_ack.items():
            if header in failed_identities:
                for identity in items:
                    if identity not in failed_identities:
                        failed.append({"identity": identity, "code": "invalid_dependency",
                                       "message": "the execution header did not apply"})
                        failed_identities.add(identity)
        # A deleted question or knowledge point queues its Paper file write in
        # the same way its writer does; publish those intents after committing.
        paper_progress.flush_files(pool)
        _atomic_json(state_path, state)
        status = "conflict" if unresolved else ("partial" if failed else "success")
        return {"status": status, "course": state["course"], "origin": state["origin"],
                "applied": applied, "kept": kept, "failed": failed,
                "conflicts": [{"identity": item["identity"], "base": item.get("base"),
                               "local": item.get("local"), "incoming": item.get("incoming")}
                              for item in unresolved],
                "base_size": len(state["base"]),
                "local": {"applied": len(applied)}, "remote": None}


def _execution_unit_ready(asset):
    """A unit this receiver can rebuild, checked before any write is attempted."""
    content = asset.get("content")
    if not isinstance(content, dict):
        return False
    if asset["kind"] == "execution_item":
        return isinstance(content.get("position"), int) and isinstance(content.get("execution_id"), str)
    return isinstance(content.get("execution_id"), str)


def _with_group_dependencies(changes):
    """A header also waits for the dependencies its grouped items declare.

    `_execution_units` moves items out of the unit list, so the header alone would
    be ordered only by its own `depends_on` and could run before an attempt row it
    must resolve (C05 F1a).
    """
    grouped = {}
    for change in changes:
        if change["asset"]["kind"] == "execution_item":
            grouped.setdefault(change["identity"].rsplit("/item/", 1)[0], set()).update(
                key for key in change["asset"].get("depends_on", []) if key)
    if not grouped:
        return changes
    extended = []
    for change in changes:
        identity = change["identity"]
        # An item always depends on its own header; keeping that edge would make
        # the header wait for itself and block the whole group.
        extra = {key for key in grouped.get(identity, ())
                 if key != identity and not key.startswith(identity + "/item/")}
        if not extra:
            extended.append(change)
            continue
        asset = dict(change["asset"])
        asset["depends_on"] = sorted(set(asset.get("depends_on", [])) | extra)
        extended.append({**change, "asset": asset})
    return extended


def _receive_chunks(ordered):
    """Publish file intents before any following row can depend on their bytes."""
    chunk = []
    for change in ordered:
        if chunk and (len(chunk) == 128 or
                      (change["asset"]["kind"] == "file") != (chunk[-1]["asset"]["kind"] == "file")):
            yield chunk
            chunk = []
        chunk.append(change)
    if chunk:
        yield chunk


def _supported_units(changes):
    """Reserved for units a future receiver cannot write; every v1 kind is writable now."""
    return list(changes), set()


def _execution_units(changes, local_assets):
    """Group each execution header with every item known for it, local or incoming."""
    headers = {}
    incoming_items = {}
    local_items = {}
    for change in changes:
        asset = change["asset"]
        if asset["kind"] == "execution":
            headers[change["identity"]] = change
        elif asset["kind"] == "execution_item" and asset.get("content"):
            header = change["identity"].rsplit("/item/", 1)[0]
            incoming_items.setdefault(header, {})[asset["content"]["position"]] = asset
    for identity, asset in local_assets.items():
        if asset.get("kind") == "execution_item" and asset.get("content"):
            header = identity.rsplit("/item/", 1)[0]
            local_items.setdefault(header, {})[asset["content"]["position"]] = asset
    grouped = {}
    for identity in headers:
        merged = dict(local_items.get(identity, {}))
        merged.update(incoming_items.get(identity, {}))
        grouped[identity] = merged
    return headers, grouped


def _write_execution(pool, connection, state, index, identity, asset, items):
    """Rebuild an active run or a parked checkpoint from its projected units."""
    if asset.get("deleted"):
        _retire_execution(connection, state, index, identity, asset)
        return
    content = dict(asset["content"])
    presentation = asset.get("presentation") or {}
    declared = content.pop("items", None)
    record = {key: value for key, value in content.items() if key != "paper_id"}
    record["execution_id"] = _local_identifier(content.get("execution_id"), index)
    ordered = _execution_items(declared, items)
    record["items"] = [_item_record(item, index) for item in ordered]
    paper_id = content.get("paper_id") or content.get("source_ref")
    generation = content.get("paper_generation") or 1
    record["paper_generation"] = generation
    if presentation.get("selected"):
        _write_active(connection, record, presentation)
    else:
        _write_checkpoint(connection, record, presentation, paper_id, generation)


def _execution_items(declared, items):
    """The items the sender still holds, in its order.

    `declared` is the header's own item list; `items` are the changed item units.
    A local item that is not declared has been removed by the sender and is
    dropped, and a declared item without an incoming unit keeps its local row.
    Packages written before the header carried its item list fall back to the
    position merge.
    """
    if not isinstance(declared, list):
        return [items[position] for position in sorted(items)]
    chosen = []
    for entry in declared:
        # `items` already holds the incoming unit for a changed position and the
        # local row for an unchanged one; a position the sender does not declare
        # is a removed question and must not survive.
        asset = items.get(entry.get("position"))
        if asset is not None:
            chosen.append(asset)
    return chosen


def _retire_execution(connection, state, index, identity, asset):
    """A tombstone only clears a run the newer Paper generation replaced."""
    generation = (asset.get("content") or {}).get("paper_generation") or asset.get("presentation", {}).get(
        "paper_generation") or 0
    paper_id = (asset.get("content") or {}).get("paper_id") or asset.get("content", {}).get("source_ref")
    execution_id = (asset.get("content") or {}).get("execution_id")
    local = index.get(execution_id, (None, None))[1] if execution_id in index else None
    if local is not None and _table_exists(connection, "active_practice"):
        row = connection.execute("SELECT execution_id FROM active_practice").fetchone()
        if row is not None and row["execution_id"] == local:
            connection.execute("DELETE FROM active_practice_items")
            connection.execute("DELETE FROM active_practice")
    if paper_id and _table_exists(connection, "paper_state"):
        row = connection.execute("SELECT generation, checkpoint_json FROM paper_state "
                                 "WHERE paper_id=?", (paper_id,)).fetchone()
        if row is not None and row["checkpoint_json"]:
            parked = json.loads(row["checkpoint_json"])
            if parked.get("execution_id") == local and generation > (parked.get("paper_generation") or 0):
                connection.execute("UPDATE paper_state SET checkpoint_json=NULL WHERE paper_id=?",
                                   (paper_id,))


def _item_record(asset, index):
    item = dict(asset["content"])
    for key in ("paper_id", "paper_generation"):
        item.pop(key, None)
    item.pop("execution_id", None)
    item["attempt_id"] = _local_identifier(item.get("attempt_id"), index)
    item["draft"] = references.convert_draft(item.pop("draft", {}) or {},
                                             lambda target, value: _local_identifier(value, index))
    item["draft_sequence"] = (asset.get("presentation") or {}).get("draft_sequence", 0)
    return item


def _active_item_row(item):
    row = {key: value for key, value in item.items() if key != "draft"}
    row["draft_json"] = json.dumps(item.get("draft") or {}, ensure_ascii=False)
    return row


def _write_execution_item(connection, index, identity, asset):
    """One item changed while its execution header is unchanged on both sides."""
    content = asset["content"]
    item = _item_record(asset, index)
    execution_id = _local_identifier(content.get("execution_id"), index)
    if _table_exists(connection, "active_practice"):
        active = connection.execute("SELECT execution_id FROM active_practice").fetchone()
        if active is not None and active["execution_id"] == execution_id:
            columns = set(_column_names(connection, "active_practice_items"))
            values = {key: value for key, value in _active_item_row(item).items()
                      if key in columns}
            connection.execute(
                f'INSERT OR REPLACE INTO active_practice_items '
                f'({",".join(f'"{key}"' for key in values)}) '
                f'VALUES ({",".join("?" for _ in values)})', tuple(values.values()))
            return
    paper_id = content.get("paper_id") or content.get("source_ref")
    if paper_id and _table_exists(connection, "paper_state"):
        row = connection.execute("SELECT checkpoint_json FROM paper_state WHERE paper_id=?",
                                 (paper_id,)).fetchone()
        if row is not None and row["checkpoint_json"]:
            parked = json.loads(row["checkpoint_json"])
            if parked.get("execution_id") == execution_id:
                items = parked.get("items") or []
                position = item["position"]
                if not 0 <= position < len(items):
                    raise ValueError(f"the parked execution has no position {position}")
                items[position] = item
                connection.execute(
                    "UPDATE paper_state SET checkpoint_json=? WHERE paper_id=?",
                    (json.dumps(parked, ensure_ascii=False), paper_id))
                return
    raise ValueError("the execution this item belongs to is not present locally")


def _local_identifier(value, index):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if value not in index:
        raise ValueError(f"unresolved incoming reference: {value}")
    return index[value][1]


def _write_active(connection, record, presentation):
    columns = set(_column_names(connection, "active_practice"))
    row = {
        "singleton": 1,
        "source_kind": record.get("source_kind"),
        "source_ref": record.get("source_ref"),
        "source_label": record.get("source_label"),
        "kp_ids_json": json.dumps(record.get("kp_ids") or [], ensure_ascii=False),
        "practice_mode": record.get("practice_mode"),
        "rating_mode": record.get("rating_mode"),
        "cursor": presentation.get("cursor") or 0,
        "started_at": record.get("started_at") or _now(connection),
        "updated_at": presentation.get("updated_at") or record.get("updated_at") or _now(connection),
        "execution_id": record["execution_id"],
        "paper_generation": record.get("paper_generation") or 1,
        "reveal_timing": record.get("reveal_timing"),
    }
    row = {key: value for key, value in row.items() if key in columns}
    connection.execute(
        f'INSERT OR REPLACE INTO active_practice ({",".join(f'"{key}"' for key in row)}) '
        f'VALUES ({",".join("?" for _ in row)})', tuple(row.values()))
    connection.execute("DELETE FROM active_practice_items")
    item_columns = set(_column_names(connection, "active_practice_items"))
    for item in record["items"]:
        values = {key: value for key, value in _active_item_row(item).items()
                  if key in item_columns}
        connection.execute(
            f'INSERT INTO active_practice_items ({",".join(f'"{key}"' for key in values)}) '
            f'VALUES ({",".join("?" for _ in values)})', tuple(values.values()))
    _clear_checkpoint_of(connection, record["paper_id"] if "paper_id" in record
                         else record.get("source_ref"), record["execution_id"])


def _clear_checkpoint_of(connection, paper_id, execution_id):
    if not paper_id or not _table_exists(connection, "paper_state"):
        return
    row = connection.execute("SELECT checkpoint_json FROM paper_state WHERE paper_id=?",
                             (paper_id,)).fetchone()
    if row is None or not row["checkpoint_json"]:
        return
    parked = json.loads(row["checkpoint_json"])
    if parked.get("execution_id") == execution_id:
        connection.execute("UPDATE paper_state SET checkpoint_json=NULL WHERE paper_id=?",
                           (paper_id,))


def _write_checkpoint(connection, record, presentation, paper_id, generation):
    if not paper_id:
        raise ValueError("a parked execution needs its Paper identity")
    record["cursor"] = presentation.get("cursor") or record.get("cursor") or 0
    record["updated_at"] = presentation.get("updated_at") or record.get("updated_at") or _now(connection)
    if presentation.get("progress") is not None:
        record["progress"] = presentation["progress"]
    row = connection.execute("SELECT generation FROM paper_state WHERE paper_id=?",
                             (paper_id,)).fetchone()
    if row is not None and (row["generation"] or 1) > generation:
        raise ValueError("the incoming execution belongs to an older Paper generation")
    body = json.dumps(record, ensure_ascii=False)
    if row is None:
        connection.execute(
            "INSERT INTO paper_state (paper_id, generation, checkpoint_json) VALUES (?,?,?)",
            (paper_id, generation, body))
    else:
        connection.execute(
            "UPDATE paper_state SET generation=?, checkpoint_json=? WHERE paper_id=?",
            (max(generation, row["generation"] or 1), body, paper_id))
    if _table_exists(connection, "active_practice"):
        active = connection.execute("SELECT execution_id FROM active_practice").fetchone()
        if active is not None and active["execution_id"] == record["execution_id"]:
            connection.execute("DELETE FROM active_practice_items")
            connection.execute("DELETE FROM active_practice")


def _column_names(connection, table):
    return [row["name"] for row in connection.execute(f'PRAGMA table_info("{table}")')]


def _now(connection):
    return connection.execute("SELECT datetime('now')").fetchone()[0]


def _write_unit(pool, connection, state, index, change):
    asset = change["asset"]
    if asset["kind"] != "row":
        raise ValueError(f"unsupported asset kind: {asset['kind']}")
    identity = change["identity"]
    content = asset.get("content") or {}
    table = content.get("table")
    deletion = change["action"] == "delete" or bool(asset.get("deleted"))
    if table is None and deletion:
        encoded = _identity_key(identity)
        table = encoded[0] if encoded else None
    if deletion and table in {"problems", "knowledge_points"}:
        # Deletion keeps the effects its own writer owns: a question leaves its
        # Papers, a knowledge point takes its cards, questions and relations.
        object_id = _deleted_object_id(identity, content, table)
        if table == "problems":
            content_data._delete_problem(connection, object_id, pool)
        else:
            content_data._delete_kp(connection, object_id, pool)
        return
    if change["action"] == "delete" and not content:
        _delete_row(connection, index, identity)
        return
    table, row = _local_row(asset, index)
    if table in HISTORY_TABLES:
        # This receiver owns the history table; a pool that predates it is
        # migrated here, at the first write, never at start-up.
        from workbench.data.pool import ensure_paper_lifecycle_schema
        ensure_paper_lifecycle_schema(connection)
    keys = _primary_key(connection, table)
    if not keys:
        raise ValueError(f"target table has no persistent key: {table}")
    if table == "part_grading_jobs":
        if row.get("status") in {"pending", "running"}:
            raise ValueError("a waiting grading job is not dispatched by an import")
        # A conversation and turn belong to the machine that ran them; keeping the
        # names here would hide the target's own conversation from its learner.
        row["conversation_id"] = None
        row["turn_id"] = None
    if table == "problems" and change["action"] != "create":
        _update_problem(connection, row)
        return
    if table in IDENTITY_TABLES:
        if change["action"] == "delete" or asset.get("deleted"):
            # A tombstone keeps the row (problems) or is already gone.
            if identity not in index:
                return
            row["id"] = index[identity][1]
            change = {**change, "action": "update"}
        elif change["action"] == "create":
            row.pop("id", None)
            _insert_row(connection, table, row)
            row["id"] = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            key = json.dumps([row[name] for name in keys],
                             ensure_ascii=False, separators=(",", ":"))
            index[identity] = (table, row["id"])
            state["row_identities"][table + "/" + key] = identity
            return
        existing = index.get(identity)
        if existing is None:
            raise ValueError(f"unknown local record for {identity}")
        row["id"] = existing[1]
        _update_row(connection, table, row, ("id",))
        return
    if table in HISTORY_TABLES:
        _write_history(connection, state, change, row)
        return
    if change["action"] == "create":
        _insert_row(connection, table, row)
        return
    _update_row(connection, table, row, tuple(keys))


def _write_history(connection, state, change, row):
    """Append a received history row under a sequence local to this installation.

    Two machines can both write sequence 3 for one Paper; the identity carries the
    origin, so the receiver appends its own next number and records that mapping.
    """
    from workbench.data.pool import ensure_paper_lifecycle_schema
    ensure_paper_lifecycle_schema(connection)
    identity = change["identity"]
    paper_id = row["paper_id"]
    local = _history_sequence_of(state, identity)
    if change["action"] == "update" and local is not None:
        row["sequence"] = local
        _update_row(connection, "retired_paper_items", row, ("paper_id", "sequence"))
        return
    current = connection.execute(
        "SELECT COALESCE(MAX(sequence), 0) FROM retired_paper_items WHERE paper_id=?",
        (paper_id,)).fetchone()[0]
    row["sequence"] = current + 1
    _insert_row(connection, "retired_paper_items", row)
    state["row_identities"]["retired_paper_items/" + json.dumps(
        [paper_id, row["sequence"]], ensure_ascii=False, separators=(",", ":"))] = identity


def _history_sequence_of(state, identity):
    prefix = "retired_paper_items/"
    for local_key, mapped in state["row_identities"].items():
        if mapped == identity and local_key.startswith(prefix):
            try:
                return json.loads(local_key[len(prefix):])[1]
            except (ValueError, IndexError, TypeError):
                return None
    return None


def _deleted_object_id(identity, content, table):
    row = content.get("row") or {}
    column = "problem_id" if table == "problems" else "kp_id"
    if row.get(column) is not None:
        return row[column]
    encoded = _identity_key(identity)
    if encoded is None or encoded[0] != table or not encoded[1]:
        raise ValueError(f"cannot address the deleted asset: {identity}")
    return encoded[1][0]


def _update_problem(connection, row):
    """An imported question edit keeps the revision and draft consequences."""
    problem_id = row["problem_id"]
    try:
        before = connection.execute("SELECT * FROM problems WHERE problem_id=?",
                                    (problem_id,)).fetchone()
    except sqlite3.Error:
        before = None
    columns = set(_column_names(connection, "problems"))
    assignments = [(name, value) for name, value in row.items() if name != "problem_id"]
    if before is not None and any(name in row and before[name] != row[name]
                                  for name in content_data.CONTENT_AXES):
        assignments.extend((name, None) for name in content_data.DIFFICULTY_COLUMNS
                           if name in columns and name not in row)
    sql = (f'UPDATE problems SET {",".join(f'"{name}"=?' for name, _ in assignments)} '
           f'WHERE problem_id=?')
    paper_progress.update_question(
        connection, sql, tuple(value for _, value in assignments) + (problem_id,))


def _insert_row(connection, table, row):
    columns = list(row)
    if not columns:
        connection.execute(f'INSERT INTO "{table}" DEFAULT VALUES')
        return
    connection.execute(
        f'INSERT INTO "{table}" ({",".join(f'"{name}"' for name in columns)}) '
        f'VALUES ({",".join("?" for _ in columns)})',
        tuple(row[name] for name in columns))


def _delete_row(connection, index, identity):
    """Remove one entity named only by its persisted identity."""
    encoded = _identity_key(identity)
    if encoded is None:
        raise ValueError(f"cannot address the deleted asset: {identity}")
    table, key = encoded
    if table in IDENTITY_TABLES:
        if identity in index:
            connection.execute(f'DELETE FROM "{table}" WHERE id=?', (index[identity][1],))
        return
    keys = _primary_key(connection, table)
    if len(keys) != len(key):
        raise ValueError(f"cannot address the deleted asset: {identity}")
    connection.execute(
        f'DELETE FROM "{table}" WHERE ' + " AND ".join(f'"{name}"=?' for name in keys),
        tuple(key))


def _update_row(connection, table, row, where):
    assignments = [name for name in row if name not in where]
    connection.execute(
        f'UPDATE "{table}" SET {",".join(f'"{name}"=?' for name in assignments)} '
        f'WHERE {" AND ".join(f'"{name}"=?' for name in where)}',
        tuple(row[name] for name in assignments) + tuple(row[name] for name in where))


def _file_payload(root, change, *, db_path=None):
    content = change["asset"]["content"]
    root = _resolved_root(root)
    target = _relative(root, content.get("path"))
    relative = target.relative_to(root)
    if db_path is not None and target == Path(db_path).resolve():
        raise ValueError("a portable file cannot replace the course database")
    if any(part in {"jobs", ".git", "course-sync"} for part in relative.parts) \
            or target.name in {".env", ".credentials.yaml"}:
        raise ValueError(f"path is not a portable course asset: {relative.as_posix()}")
    data = None if change["action"] == "delete" else base64.b64decode(content["data"], validate=True)
    return target, data


def _write_file(root, change):
    target, data = _file_payload(root, change)
    if change["action"] == "delete":
        target.unlink(missing_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # A publication killed between write and replace leaves "<name>.<random>.tmp";
    # the course folder scan counts every file, so an orphan would travel as an asset.
    prefix = target.name + "."
    for entry in target.parent.iterdir():
        if entry.is_file() and entry.name.startswith(prefix) and entry.name.endswith(".tmp"):
            entry.unlink(missing_ok=True)
    handle, name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def read_exchange(source):
    """Read validated envelopes, retaining missing-file errors for the planner."""
    source = Path(source).resolve()
    manifest = _read_json(source / "manifest.json")
    if not isinstance(manifest, dict) or type(manifest.get("format_version")) is not int \
            or manifest["format_version"] not in {1, 2}:
        raise ValueError("unsupported course exchange format_version")
    if not isinstance(manifest.get("course"), dict) or not all(
            isinstance(manifest["course"].get(key), str) and manifest["course"][key]
            for key in ("id", "origin")):
        raise ValueError("invalid course origin")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", manifest["course"]["id"]):
        raise ValueError("invalid course identifier")
    if not isinstance(manifest.get("assets"), list) or not isinstance(manifest.get("base"), dict):
        raise ValueError("invalid asset manifest or base")
    loaded, errors = course_bundle.load(source, manifest["assets"], manifest["format_version"],
                                        _relative, _read_json)
    assets = {}
    for descriptor in manifest["assets"]:
        identity = descriptor["identity"]
        if identity not in loaded:
            continue
        asset = loaded[identity]
        if not isinstance(asset, dict) or asset.get("kind") not in {"row", "file", "execution", "execution_item"} \
                or asset.get("kind") != descriptor.get("kind") \
                or not (isinstance(asset.get("content"), dict)
                        or asset.get("deleted") is True and "content" not in asset) \
                or type(asset.get("deleted", False)) is not bool \
                or not isinstance(asset.get("depends_on", []), list) \
                or not all(isinstance(key, str) and key for key in asset.get("depends_on", [])):
            errors.append({"identity": identity, "code": "invalid_asset", "message": "invalid asset envelope"})
            continue
        asset = {**asset, "depends_on": asset.get("depends_on", [])}
        content = asset.get("content")
        if content is None:
            if asset["kind"] in {"execution", "execution_item"}:
                errors.append({"identity": identity, "code": "invalid_asset",
                               "message": "execution deletion requires its identifying content"})
                continue
            if asset["kind"] == "file":
                if not identity.startswith("file/"):
                    errors.append({"identity": identity, "code": "invalid_asset",
                                   "message": "file deletion requires its relative path"})
                    continue
                relative = identity[len("file/"):]
                _relative(source, relative)
                asset = {**asset, "content": {"path": relative, "encoding": "base64", "data": ""}}
            assets[identity] = asset
            continue
        if asset["kind"] == "row" and (content.get("table") not in TABLES
                                        or not isinstance(content.get("row"), dict)
                                        or not isinstance(content.get("key"), list)):
            errors.append({"identity": identity, "code": "invalid_asset", "message": "invalid row projection"})
            continue
        if asset["kind"] in {"execution", "execution_item"}:
            valid = bool(content)
            if asset["kind"] == "execution_item":
                valid = (valid and type(content.get("position")) is int
                         and content["position"] >= 0
                         and identity.endswith("/item/" + str(content["position"])))
            if not valid:
                errors.append({"identity": identity, "code": "invalid_asset",
                               "message": "invalid execution projection"})
                continue
        if asset["kind"] == "file":
            _relative(source, content.get("path"))
            try:
                if content.get("encoding") != "base64":
                    raise ValueError("unsupported file encoding")
                base64.b64decode(content.get("data", ""), validate=True)
            except (ValueError, TypeError) as exc:
                errors.append({"identity": identity, "code": "invalid_asset", "message": str(exc)})
                continue
        assets[identity] = asset
    _adopt_edited_copies(source, assets, {item["identity"] for item in manifest["assets"]}, errors)
    return {**manifest, "assets": assets, "errors": errors}


def _adopt_edited_copies(source, assets, declared, errors):
    """A Tutor edits the plain copy; an edited copy is the asset's content.

    The envelopes stay the exchange format, so a readable folder that disagrees
    with its envelope means the Tutor changed the file after the export. Taking
    that copy is what makes the returned update receivable at all.
    """
    folder = Path(source) / READABLE_DIR
    if not folder.is_dir():
        return
    for identity, asset in assets.items():
        if asset.get("kind") != "file" or asset.get("deleted"):
            continue
        content = asset.get("content") or {}
        try:
            edited = _relative(folder, content.get("path"))
        except ValueError:
            continue
        if not edited.is_file():
            continue
        data = edited.read_bytes()
        if base64.b64encode(data).decode("ascii") == content.get("data"):
            continue
        asset["content"] = {**content, "data": base64.b64encode(data).decode("ascii")}
        asset["readable_copy"] = True

    # A new plain file is an explicit creation. Missing files never imply deletion;
    # an invalid declared envelope cannot be bypassed by its readable copy.
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(folder).as_posix()
        identity = "file/" + relative
        if identity in declared or identity in assets:
            continue
        try:
            target = _relative(folder, relative)
            asset = {"kind": "file", "content": {"path": relative, "encoding": "base64",
                     "data": base64.b64encode(target.read_bytes()).decode("ascii")}, "depends_on": []}
            _file_payload(folder, {"asset": asset, "action": "create"})
        except (OSError, ValueError) as exc:
            errors.append({"identity": identity, "code": "invalid_asset", "message": str(exc)})
            continue
        assets[identity] = asset
