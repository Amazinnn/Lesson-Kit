"""Small explicit workspace-local goal store."""

import json
from pathlib import Path


def _path(root):
    return Path(root) / ".lessonkit" / "goals.json"


def list_goals(root):
    path = _path(root)
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return value if isinstance(value, list) else []


def create_goal(root, values):
    values = values if isinstance(values, dict) else {}
    title = str(values.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    goals = list_goals(root)
    numbers = [
        int(item["id"].split("-")[-1])
        for item in goals
        if isinstance(item, dict) and str(item.get("id", "")).startswith("goal-")
        and str(item["id"]).split("-")[-1].isdigit()
    ]
    goal = {
        "id": f"goal-{max(numbers, default=0) + 1:03d}",
        "kind": values.get("kind") or "stage",
        "title": title,
        "deadline": values.get("deadline") or None,
        "description": str(values.get("description") or "").strip() or None,
        "scope": str(values.get("scope") or "").strip() or None,
    }
    goals.append(goal)
    _write(root, goals)
    return goal


def update_goal(root, goal_id, values):
    goals = list_goals(root)
    for goal in goals:
        if goal.get("id") != goal_id:
            continue
        for key in ("kind", "deadline", "description", "scope"):
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


def delete_goal(root, goal_id):
    goals = list_goals(root)
    remaining = [goal for goal in goals if goal.get("id") != goal_id]
    if len(remaining) == len(goals):
        raise KeyError(goal_id)
    _write(root, remaining)
    return {"id": goal_id, "deleted": True}


def _write(root, goals):
    path = _path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(goals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
