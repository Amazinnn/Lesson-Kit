"""Binary figure projection for the version-controlled authored-content repository.

Figure bytes stay outside SQLite. The pool owns logical references, while a
checked-out content repository versions the corresponding bytes under
``figures/<course>/...``. A derived UTF-8 index makes old hash-named figures
locatable by problem/knowledge-point id without turning that index into a second
authority. Git transport remains outside Lesson Kit.

During the layout transition a workspace may hold the same logical figure in the
new top-level ``figures/`` area or in the legacy ``.lessonkit/figures/`` runtime
area. Push prefers the top-level copy and falls back to the legacy copy. Pull
writes both so today's workbench keeps rendering while local agents can migrate
without a flag day.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path, PurePosixPath


FIGURE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "svg", "webp"}
FIGURE_TABLES = (
    ("kp", "knowledge_points", "kp_id"),
    ("problem", "problems", "problem_id"),
)
DIRECTIONS = {"check", "push", "pull"}
INDEX_SCHEMA_VERSION = 1


class FigureMirrorError(ValueError):
    """Readable contract failure for the binary figure projection."""


def _columns(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if row is None:
        return set()
    return {str(item[1]) for item in conn.execute(f"PRAGMA table_info({table})")}


def _decode_paths(raw, owner_id):
    if raw is None or raw == "":
        return []
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        raise FigureMirrorError(f"{owner_id}: figure_paths is invalid JSON") from exc
    if not isinstance(value, list):
        raise FigureMirrorError(f"{owner_id}: figure_paths must be a JSON array")
    paths = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise FigureMirrorError(
                f"{owner_id}: every figure_paths entry must be a non-empty string"
            )
        paths.append(item.strip())
    return paths


def _logical_path(course, logical):
    """Validate one pool-stored POSIX logical path without normalizing damage away."""
    if not isinstance(course, str) or not course:
        raise FigureMirrorError("workspace has no active course for figure synchronization")
    if not isinstance(logical, str) or not logical:
        raise FigureMirrorError("figure path must be a non-empty string")
    if "\\" in logical or logical.startswith("/"):
        raise FigureMirrorError(f"figure path must be workspace-relative POSIX: {logical}")
    raw_parts = logical.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise FigureMirrorError(f"figure path may not escape or contain empty parts: {logical}")
    path = PurePosixPath(logical)
    if len(path.parts) < 3 or path.parts[0] != course:
        raise FigureMirrorError(
            f"figure path must start with {course}/<chapter>/: {logical}"
        )
    extension = path.suffix.lstrip(".").lower()
    if extension not in FIGURE_EXTENSIONS:
        raise FigureMirrorError(f"unsupported figure extension in {logical}")
    return path


def references(pool):
    """Return unique logical figures and every authored object that references them."""
    if not Path(pool.db_path).is_file():
        raise FigureMirrorError("figure synchronization requires an existing pool database file")
    conn = pool.connect()
    grouped = {}
    for owner_type, table, id_column in FIGURE_TABLES:
        columns = _columns(conn, table)
        if not columns:
            raise FigureMirrorError(
                f"pool database is missing required figure owner table: {table}"
            )
        if id_column not in columns:
            raise FigureMirrorError(
                f"pool database figure owner table is missing {id_column}: {table}"
            )
        if "figure_paths" not in columns:
            continue
        rows = conn.execute(
            f"SELECT {id_column}, figure_paths FROM {table} "
            "WHERE figure_paths IS NOT NULL AND figure_paths <> '' "
            f"ORDER BY {id_column}"
        ).fetchall()
        for owner_id, raw in rows:
            for logical in _decode_paths(raw, owner_id):
                _logical_path(pool.course, logical)
                grouped.setdefault(logical, []).append({
                    "owner_type": owner_type,
                    "owner_id": str(owner_id),
                })
    return [
        {"logical": logical, "owners": grouped[logical]}
        for logical in sorted(grouped)
    ]


def _safe_target(root, course, logical, anchor):
    anchor = Path(anchor).resolve()
    root = Path(root).resolve()
    if not root.is_relative_to(anchor):
        raise FigureMirrorError("figure asset root leaves its workspace or checkout")
    path = _logical_path(course, logical)
    target = (root / Path(*path.parts)).resolve()
    if not target.is_relative_to(root) or not target.is_relative_to(anchor):
        raise FigureMirrorError(f"figure path leaves its asset root: {logical}")
    return target


def repo_path(repo, course, logical):
    repo_root = Path(repo).resolve()
    return _safe_target(repo_root / "figures", course, logical, repo_root)


def workspace_paths(pool, logical):
    workspace_root = Path(pool.root).resolve()
    canonical = _safe_target(
        workspace_root / "figures", pool.course, logical, workspace_root
    )
    legacy = _safe_target(
        workspace_root / ".lessonkit" / "figures", pool.course, logical,
        workspace_root,
    )
    return canonical, legacy


def index_path(repo, course):
    if (not isinstance(course, str) or not course or course in {".", ".."}
            or "/" in course or "\\" in course):
        raise FigureMirrorError(f"invalid course id for figure index: {course!r}")
    repo_root = Path(repo).resolve()
    asset_root = (repo_root / "figures").resolve()
    if not asset_root.is_relative_to(repo_root):
        raise FigureMirrorError("figure index asset root leaves its checkout")
    target = (asset_root / course / "_index.json").resolve()
    if not target.is_relative_to(asset_root) or not target.is_relative_to(repo_root):
        raise FigureMirrorError("figure index path leaves its checkout")
    return target


def _index_value(course, refs):
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "course_id": course,
        "figures": [
            {"logical_path": item["logical"], "owners": item["owners"]}
            for item in refs
        ],
    }


def _index_bytes(course, refs):
    return (json.dumps(_index_value(course, refs), ensure_ascii=False, indent=2)
            + "\n").encode("utf-8")


def _index_status(repo, course, refs):
    path = index_path(repo, course)
    expected = _index_bytes(course, refs)
    if not path.is_file():
        return {"path": str(path), "status": "missing"}
    try:
        actual = path.read_bytes()
        value = json.loads(actual.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "status": "invalid", "error": str(exc)}
    if not isinstance(value, dict):
        return {"path": str(path), "status": "invalid",
                "error": "figure index must be a JSON object"}
    return {"path": str(path), "status": "same" if actual == expected else "different"}


def _workspace_source(pool, logical):
    canonical, legacy = workspace_paths(pool, logical)
    if canonical.is_file():
        return canonical, "workspace"
    if legacy.is_file():
        return legacy, "legacy_workspace"
    return None, None


def _same_bytes(left, right):
    return left.is_file() and right.is_file() and left.read_bytes() == right.read_bytes()


def _legacy_hash_identity(logical):
    stem = PurePosixPath(logical).stem
    return len(stem) == 64 and all(char in "0123456789abcdef" for char in stem)


def plan(pool, repo, direction="check"):
    """Classify every pool-referenced figure without writing any file."""
    if direction not in DIRECTIONS:
        raise FigureMirrorError(
            f"unsupported figure mirror direction: {direction}; expected check, push, or pull"
        )
    repo = Path(repo).resolve()
    items = []
    try:
        refs = references(pool)
    except FigureMirrorError as exc:
        return {
            "kind": "figure-mirror", "course": pool.course, "direction": direction,
            "valid": False, "items": [{"status": "invalid", "error": str(exc)}],
            "index": {"status": "not_checked"},
        }

    index = _index_status(repo, pool.course, refs)
    for ref in refs:
        logical = ref["logical"]
        target = repo_path(repo, pool.course, logical)
        source, source_kind = _workspace_source(pool, logical)
        canonical, legacy = workspace_paths(pool, logical)
        item = {
            **ref,
            "repository_path": str(target),
            "workspace_path": str(canonical),
            "legacy_workspace_path": str(legacy),
        }
        if _legacy_hash_identity(logical):
            copies = [path for path in (target, canonical, legacy) if path.is_file()]
            if (direction == "pull" and target.is_file()
                    and not canonical.is_file() and not legacy.is_file()):
                item.update({
                    "status": "conflict",
                    "error": "hash-named repository figure has no workspace baseline",
                })
                items.append(item)
                continue
            if copies and any(not _same_bytes(copies[0], path) for path in copies[1:]):
                item.update({
                    "status": "conflict",
                    "error": "existing hash-named figure copies contain different bytes",
                })
                items.append(item)
                continue
        if direction == "push":
            if source is None:
                item.update({
                    "status": "invalid",
                    "error": f"workspace figure is missing: {logical}",
                })
            elif not target.is_file():
                item.update({"status": "create", "source": source_kind})
            elif _same_bytes(source, target):
                item.update({"status": "noop", "source": source_kind})
            else:
                item.update({"status": "update", "source": source_kind})
        elif direction == "pull":
            if not target.is_file():
                item.update({
                    "status": "invalid",
                    "error": f"repository figure is missing: {logical}",
                })
            elif _same_bytes(target, canonical) and _same_bytes(target, legacy):
                item["status"] = "noop"
            elif not canonical.is_file() and not legacy.is_file():
                item["status"] = "create"
            else:
                item["status"] = "update"
        else:
            if not target.is_file() and source is None:
                item.update({
                    "status": "invalid",
                    "error": f"figure is missing from repository and workspace: {logical}",
                })
            elif not target.is_file():
                item.update({"status": "repository_missing", "source": source_kind})
            elif source is None:
                item["status"] = "workspace_missing"
            elif _same_bytes(source, target):
                item.update({"status": "same", "source": source_kind})
            else:
                item.update({"status": "different", "source": source_kind})
        items.append(item)

    return {
        "kind": "figure-mirror",
        "course": pool.course,
        "direction": direction,
        "valid": not any(item["status"] in {"invalid", "conflict"} for item in items),
        "items": items,
        "index": index,
    }


def _atomic_copy(source, target):
    source = Path(source)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_bytes(target, content):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def sync(pool, repo, direction, dry_run=False):
    """Apply an explicit binary direction; never chooses a winner on its own."""
    if direction == "check":
        report = plan(pool, repo, "check")
        if dry_run:
            report["dry_run"] = True
        return report
    report = plan(pool, repo, direction)
    if dry_run or not report["valid"]:
        if dry_run:
            report["dry_run"] = True
        return report

    for item in report["items"]:
        if item["status"] == "noop":
            continue
        logical = item["logical"]
        target = repo_path(repo, pool.course, logical)
        if direction == "push":
            source, _ = _workspace_source(pool, logical)
            if source is None:  # plan already guarded this; keep the write boundary explicit.
                raise FigureMirrorError(f"workspace figure disappeared before push: {logical}")
            _atomic_copy(source, target)
        else:
            if not target.is_file():
                raise FigureMirrorError(f"repository figure disappeared before pull: {logical}")
            canonical, legacy = workspace_paths(pool, logical)
            _atomic_copy(target, canonical)
            _atomic_copy(target, legacy)
        item["status"] = "applied"

    if direction == "push":
        refs = references(pool)
        _atomic_write_bytes(index_path(repo, pool.course), _index_bytes(pool.course, refs))
        report["index"] = {"path": str(index_path(repo, pool.course)), "status": "applied"}
    report["applied"] = sum(item["status"] == "applied" for item in report["items"])
    return report
