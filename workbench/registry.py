"""Workspace registry and bridge provider config (user-level, JSON)."""

import json
import os
import re
from pathlib import Path

IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def base_dir():
    return Path(os.environ.get("LESSONKIT_WB_HOME", Path.home() / ".lessonkit-workbench"))


def _load_json(path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_registry():
    return _load_json(base_dir() / "workspaces.json", {"version": 1, "workspaces": []})


def save_registry(registry_data):
    _save_json(base_dir() / "workspaces.json", registry_data)


def register(path, name=None, db=None, course=None, chapter=None):
    folder = Path(path).resolve()
    if not looks_like_workspace(folder):
        raise ValueError(f"not a lesson-kit folder: {folder}")
    registry_data = load_registry()
    workspace = {
        "name": name or folder.name,
        "path": str(folder),
        "db": db or find_pool(folder, course or ""),
        "active_course": course or "",
        "active_chapter": chapter or "",
    }
    if not workspace["db"] or not (folder / workspace["db"]).resolve().is_relative_to(folder):
        raise ValueError(
            f"the pool database must live inside the workspace folder: "
            f"{workspace['db']!r}"
        )
    for other in registry_data["workspaces"]:
        if other["name"] == workspace["name"] and Path(other["path"]) != folder:
            raise ValueError(
                f"workspace name {workspace['name']!r} is already registered for "
                f"{other['path']} — pass --name <name> to keep both"
            )
        if other["name"] != workspace["name"] and Path(other["path"]) == folder:
            raise ValueError(
                f"{folder} is already registered as workspace {other['name']!r}"
            )
    workspaces = [
        w for w in registry_data["workspaces"] if w["name"] != workspace["name"]
    ]
    workspaces.append(workspace)
    registry_data["workspaces"] = workspaces
    save_registry(registry_data)
    return workspace


def list_workspaces():
    return load_registry()["workspaces"]


def get_workspace(name):
    for workspace in list_workspaces():
        if workspace["name"] == name:
            return workspace
    raise KeyError(f"unknown workspace: {name}")


def update_active(name, course, chapter):
    """Switch a workspace's active course/chapter in place; touches nothing else.

    One writer for both surfaces: the dashboard chapter lens and `lesson-kit use`.
    An empty chapter is the whole-course lens and is always accepted.
    """
    if chapter and not IDENTIFIER.fullmatch(chapter):
        raise ValueError(
            f"chapter {chapter!r} must be a lowercase ASCII identifier or empty"
        )
    registry_data = load_registry()
    for workspace in registry_data["workspaces"]:
        if workspace["name"] == name:
            workspace["active_course"] = course
            workspace["active_chapter"] = chapter
            save_registry(registry_data)
            return workspace
    raise KeyError(f"unknown workspace: {name}")


def load_bridges():
    return _load_json(base_dir() / "bridges.json", {"version": 1, "providers": {}})


def save_bridges(bridges):
    _save_json(base_dir() / "bridges.json", bridges)


def add_bridge(provider, command, args=None, cwd_mode="workspace", timeout_s=300,
               model=None):
    bridges = load_bridges()
    entry = {
        "command": command,
        "args": args or [],
        "cwd_mode": cwd_mode,
        "timeout_s": timeout_s,
    }
    if model:
        entry["model"] = model
    bridges["providers"][provider] = entry
    save_bridges(bridges)
    return bridges["providers"][provider]


def looks_like_workspace(folder):
    if (folder / "lessonkit.py").is_file():
        return True
    pool_dir = folder / "pool"
    return pool_dir.is_dir() and any(pool_dir.glob("*.db"))


def pool_candidates(folder):
    """Candidate pools of a folder, in name order; ingest backups are never candidates."""
    pool_dir = folder / "pool"
    if not pool_dir.is_dir():
        return []
    return [
        f"pool/{db.name}" for db in sorted(pool_dir.glob("*.db"))
        if not db.name.endswith(".ingest-backup")
    ]


def find_pool(folder, course=""):
    """The pool a folder registers with: `pool/<course>.db`, else its only candidate.

    Several candidates with no matching name is a refusal, not a guess: a folder may
    hold a pre-readiness copy of the pool next to the live one, and picking the
    alphabetically first would register the wrong database.
    """
    candidates = pool_candidates(folder)
    if course and f"pool/{course}.db" in candidates:
        return f"pool/{course}.db"
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return ""
    raise ValueError(
        f"{folder} holds several pool databases "
        f"({', '.join(Path(c).name for c in candidates)})\n"
        f"Pick one: lesson-kit init {folder} --course <name>"
    )
