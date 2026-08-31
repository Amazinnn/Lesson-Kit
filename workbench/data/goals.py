"""Small explicit workspace-local goal store."""

import json
import os
import tempfile
import threading
from pathlib import Path


_LOCK = threading.Lock()


def _path(root):
    return Path(root) / ".lessonkit" / "goals.json"


def list_goals(root):
    try:
        return _load(root)
    except (OSError, ValueError):
        return []


def _load(root):
    path = _path(root)
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("goals.json must contain a list of objects")
    return value


def create_goal(root, values):
    values = values if isinstance(values, dict) else {}
    title = str(values.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    _validate_period(values.get("start_date"), values.get("deadline"))
    with _LOCK:
        goals = _load(root)
        numbers = [
            int(item["id"].split("-")[-1])
            for item in goals
            if str(item.get("id", "")).startswith("goal-")
            and str(item["id"]).split("-")[-1].isdigit()
        ]
        goal = {
            "id": f"goal-{max(numbers, default=0) + 1:03d}",
            "kind": values.get("kind") or "stage",
            "title": title,
            "start_date": values.get("start_date") or None,
            "deadline": values.get("deadline") or None,
            "description": str(values.get("description") or "").strip() or None,
            "scope": str(values.get("scope") or "").strip() or None,
        }
        goals.append(goal)
        _write(root, goals)
    return goal


def update_goal(root, goal_id, values):
    with _LOCK:
        goals = _load(root)
        for goal in goals:
            if goal.get("id") != goal_id:
                continue
            if "start_date" in values or "deadline" in values:
                _validate_period(
                    values.get("start_date", goal.get("start_date")),
                    values.get("deadline", goal.get("deadline")),
                )
            for key in ("kind", "start_date", "deadline", "description", "scope"):
                if key in values:
                    goal[key] = values[key] or None
            if "title" in values:
                title = str(values.get("title") or "").strip()
                if not title:
                    raise ValueError("title is required")
                goal["title"] = title
            _write(root, goals)
            return goal
    raise KeyError(goal_id)


def _validate_period(start_date, deadline):
    if start_date and deadline and str(start_date) > str(deadline):
        raise ValueError("start_date must not be after deadline")


def delete_goal(root, goal_id):
    with _LOCK:
        goals = _load(root)
        remaining = [goal for goal in goals if goal.get("id") != goal_id]
        if len(remaining) == len(goals):
            raise KeyError(goal_id)
        _write(root, remaining)
    return {"id": goal_id, "deleted": True}


def _write(root, goals):
    path = _path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(goals, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
