"""File exchange projections of committed course data, without Git transport."""

import base64
import json
import os
import re
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from uuid import uuid4

from workbench import registry
from workbench.data import figure_mirror


FORMAT_VERSION = 1
TABLES = {
    "knowledge_points", "knowledge_relations", "problems", "flash_cards",
    "questions", "question_progress", "kp_progress", "problem_progress",
    "problem_attempts", "feedback_events", "review_schedule", "learner_signals",
    "learning_current_state", "kp_experiences", "kp_experience_problems",
    "active_practice", "active_practice_items", "paper_state", "practice_runs",
    "problem_revisions", "practice_execution_ids", "attempt_operations",
    "practice_request_operations", "part_attempt_context", "part_grading_revisions",
    "part_grading_jobs", "content_mirror_state", "content_mirror_log",
    "content_sequences", "ingest_batches", "candidate_problems",
}
IDENTITY_TABLES = {"problem_attempts", "feedback_events", "practice_runs",
                   "practice_execution_ids", "content_mirror_log", "question_progress"}
WINDOWS_DEVICE_NAMES = {"con", "prn", "aux", "nul"} | {
    prefix + str(number) for prefix in ("com", "lpt") for number in range(1, 10)}


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


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
    root = Path(root).resolve()
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
    """Serialize CLI exchange writers without guessing whether an old owner died."""
    folder = Path(root) / ".lessonkit/course-sync"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "write.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("course exchange is locked by another operation") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def _installation_origin():
    path = registry.base_dir() / "course-sync-installation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        lock = path.with_suffix(".lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError("installation origin is being initialized by another operation") from exc
        try:
            os.close(descriptor)
            if not path.exists():
                _atomic_json(path, {"origin": "installation-" + str(uuid4())})
        finally:
            lock.unlink()
    value = _read_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("origin"), str) or not value["origin"]:
        raise ValueError("invalid installation origin")
    return value["origin"]


def _state(root, course):
    path = Path(root) / ".lessonkit/course-sync/state.json"
    if path.exists():
        state = _read_json(path)
        if not isinstance(state, dict) or not isinstance(state.get("course"), dict) \
                or state["course"].get("id") != course:
            raise ValueError("course exchange state has a different course identity")
        if not isinstance(state.get("row_identities"), dict) or not isinstance(state.get("base"), dict):
            raise ValueError("invalid course exchange identity mappings or base")
        state["origin"] = _installation_origin()
        return state
    return {"course": {"id": course, "origin": "course-" + str(uuid4())},
            "origin": _installation_origin(), "row_identities": {}, "base": {}}


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
        unknown = names - TABLES
        if unknown:
            raise ValueError("unregistered course tables: " + ", ".join(sorted(unknown)))
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
            inventory.append({"table": table, "columns": [row["name"] for row in columns],
                              "primary_key": keys, "rows": len(rows)})
            for source in rows:
                row = dict(source)
                key = [row[name] for name in keys]
                spelling = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
                local_key = table + "/" + spelling
                identities = state["row_identities"]
                if local_key not in identities:
                    prefix = state["origin"] + "/" if table in IDENTITY_TABLES else ""
                    identities[local_key] = "row/" + table + "/" + prefix + spelling
                identity = identities[local_key]
                assets[identity] = {"kind": "row", "content": {"table": table, "key": keys, "row": row},
                                    "depends_on": []}
                if table == "problems" and row.get("deleted_at"):
                    assets[identity]["deleted"] = True
        return assets, inventory
    finally:
        snapshot.close()


def _managed_files(pool, assets):
    root = pool.root
    files = set()
    for name in ("goals.json", "course-preferences.json"):
        path = root / ".lessonkit" / name
        if path.exists():
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
                raise ValueError(f"missing managed course path: {name}")
            if path.is_dir():
                files.update(item for item in path.rglob("*") if item.is_file())
            else:
                files.add(path)
    for path in sorted(files):
        relative = path.relative_to(root).as_posix()
        _relative(root, relative)
        if path == pool.db_path or path.name in {".env", ".credentials.yaml"} or any(
                part in {"jobs", ".git", "course-sync"} for part in path.relative_to(root).parts):
            raise ValueError(f"path is not a portable course asset: {relative}")
        yield relative, path


def export_course(pool, workspace, destination):
    """Export a closed committed projection, rejecting unknown or missing assets."""
    destination = Path(destination).resolve()
    with course_lock(pool.root):
        state = _state(pool.root, pool.course)
        assets, inventory = _database_projection(pool, state)
        for relative, path in _managed_files(pool, assets):
            assets["file/" + relative] = {
                "kind": "file", "content": {"path": relative, "encoding": "base64",
                                             "data": base64.b64encode(path.read_bytes()).decode("ascii")},
                "depends_on": []}
        # Persist source identities before publishing anything another device can
        # receive. A failed first export must retain the same course lineage.
        _atomic_json(pool.root / ".lessonkit/course-sync/state.json", state)
        export_id = "export-" + str(uuid4())
        descriptors = []
        for identity, asset in sorted(assets.items()):
            relative = export_id + "/assets/" + quote(identity, safe="/") + ".json"
            _atomic_json(_relative(destination, relative), asset)
            descriptors.append({"identity": identity, "kind": asset["kind"], "path": relative,
                                "depends_on": asset["depends_on"]})
        manifest = {"format_version": FORMAT_VERSION, "course": state["course"],
                    "origin": state["origin"], "export_id": export_id,
                    "assets": descriptors, "base": state["base"], "tables": inventory}
        _atomic_json(destination / "manifest.json", manifest)
        state["base"] = assets
        _atomic_json(pool.root / ".lessonkit/course-sync/state.json", state)
        return {"status": "success", "course": state["course"], "origin": state["origin"],
                "export_id": export_id, "assets": len(assets), "tables": inventory,
                "destination": str(destination), "local": {"exported": True}, "remote": None}


def read_exchange(source):
    """Read validated envelopes, retaining missing-file errors for the planner."""
    source = Path(source).resolve()
    manifest = _read_json(source / "manifest.json")
    if not isinstance(manifest, dict) or type(manifest.get("format_version")) is not int \
            or manifest["format_version"] != FORMAT_VERSION:
        raise ValueError("unsupported course exchange format_version")
    if not isinstance(manifest.get("course"), dict) or not all(
            isinstance(manifest["course"].get(key), str) and manifest["course"][key]
            for key in ("id", "origin")):
        raise ValueError("invalid course origin")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", manifest["course"]["id"]):
        raise ValueError("invalid course identifier")
    if not isinstance(manifest.get("assets"), list) or not isinstance(manifest.get("base"), dict):
        raise ValueError("invalid asset manifest or base")
    assets, errors, identities, paths = {}, [], set(), set()
    for descriptor in manifest["assets"]:
        if not isinstance(descriptor, dict) or not isinstance(descriptor.get("identity"), str):
            raise ValueError("invalid asset descriptor")
        identity = descriptor["identity"]
        if not identity or identity in identities:
            raise ValueError("duplicate or empty asset identity")
        identities.add(identity)
        path = _relative(source, descriptor.get("path"))
        normalized_path = path.relative_to(source).as_posix().lower()
        if normalized_path in paths:
            raise ValueError("duplicate asset path")
        paths.add(normalized_path)
        if not path.is_file():
            errors.append({"identity": identity, "code": "missing_asset", "message": "asset file is absent"})
            continue
        try:
            asset = _read_json(path)
        except (ValueError, OSError) as exc:
            errors.append({"identity": identity, "code": "invalid_asset", "message": str(exc)})
            continue
        if not isinstance(asset, dict) or asset.get("kind") not in {"row", "file"} \
                or asset.get("kind") != descriptor.get("kind") \
                or not isinstance(asset.get("content"), dict) \
                or type(asset.get("deleted", False)) is not bool \
                or not isinstance(asset.get("depends_on", []), list) \
                or not all(isinstance(key, str) and key for key in asset.get("depends_on", [])):
            errors.append({"identity": identity, "code": "invalid_asset", "message": "invalid asset envelope"})
            continue
        content = asset["content"]
        if asset["kind"] == "row" and (content.get("table") not in TABLES
                                        or not isinstance(content.get("row"), dict)
                                        or not isinstance(content.get("key"), list)):
            errors.append({"identity": identity, "code": "invalid_asset", "message": "invalid row projection"})
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
    return {**manifest, "assets": assets, "errors": errors}
