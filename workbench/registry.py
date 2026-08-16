"""Workspace registry and bridge provider config (user-level, JSON)."""

import json
import os
from pathlib import Path


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
    if not _looks_like_workspace(folder):
        raise ValueError(f"not a lesson-kit folder: {folder}")
    registry_data = load_registry()
    workspace = {
        "name": name or folder.name,
        "path": str(folder),
        "db": db or _find_pool(folder),
        "active_course": course or "",
        "active_chapter": chapter or "",
    }
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


def load_bridges():
    return _load_json(base_dir() / "bridges.json", {"version": 1, "providers": {}})


def save_bridges(bridges):
    _save_json(base_dir() / "bridges.json", bridges)


def add_bridge(provider, command, args=None, cwd_mode="workspace", timeout_s=300):
    bridges = load_bridges()
    bridges["providers"][provider] = {
        "command": command,
        "args": args or [],
        "cwd_mode": cwd_mode,
        "timeout_s": timeout_s,
    }
    save_bridges(bridges)
    return bridges["providers"][provider]


def _looks_like_workspace(folder):
    if (folder / "lessonkit.py").is_file():
        return True
    pool_dir = folder / "pool"
    return pool_dir.is_dir() and any(pool_dir.glob("*.db"))


def _find_pool(folder):
    pool_dir = folder / "pool"
    if pool_dir.is_dir():
        for db in sorted(pool_dir.glob("*.db")):
            return f"pool/{db.name}"
    return ""
