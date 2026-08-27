"""Small, deterministic daily-plan rules.

The planner consumes facts supplied by the Data/Shell layer.  It never opens a
database and never writes learning state; an Agent may adjust its result later.
"""

from datetime import date, datetime
import math


DEFAULT_MINUTES = 45
DEFAULT_TARGET = 3


def build_baseline_plan(workspace, *, now=None, available_minutes=None):
    """Return a repeatable coarse plan for one workspace facts mapping.

    ``workspace`` is deliberately a plain mapping so callers can assemble it
    from any Data query without making the Domain depend on SQLite.
    """
    now = now or datetime.now()
    facts = workspace or {}
    minutes = _positive_int(available_minutes, DEFAULT_MINUTES)
    kps = list(facts.get("kps") or [])
    problems = list(facts.get("problems") or [])
    progress = facts.get("progress") or {}
    signals = {row.get("target_id"): row for row in facts.get("signals") or []}
    due = {
        row.get("item_id") for row in facts.get("schedule") or []
        if row.get("item_type") == "kp" and _is_due(row.get("due_at"), now)
    }
    goals = [_goal(row) for row in facts.get("goals") or []]
    if not goals:
        goals = [{
            "id": "course",
            "kind": "long_term",
            "title": "完成当前课程",
            "deadline": None,
        }]
    deadline_boost = _deadline_boost(goals, now)
    queue = []
    for kp in kps:
        kp_id = kp.get("kp_id") or ""
        if not kp_id:
            continue
        linked = [p for p in problems if kp_id in (p.get("kp_ids") or [])]
        stats = progress.get(kp_id) or {}
        total = _positive_int(stats.get("total"), len(linked))
        completed = max(0, _number(stats.get("completed"), 0))
        coverage = 0 if total <= 0 else min(1.0, completed / total)
        signal = signals.get(kp_id) or {}
        urgency = (3 if signal.get("weight") == "high" else
                   2 if signal.get("weight") == "medium" else 0)
        if kp_id in due:
            urgency += 2
        if kp.get("importance") == "core":
            urgency += 1
        target = DEFAULT_TARGET
        if coverage < 0.5:
            target += 1
        if urgency >= 3:
            target += 1
        if deadline_boost > 1:
            target += math.ceil(deadline_boost - 1)
        target = max(1, min(target, max(1, len(linked)))) if linked else 1
        types = {}
        for problem in linked:
            kind = problem.get("problem_type") or "other"
            types[kind] = types.get(kind, 0) + 1
        title = kp.get("knowledge_item") or kp_id
        reasons = []
        if coverage < 0.5:
            reasons.append("覆盖仍低")
        if kp_id in due:
            reasons.append("复习已到期")
        if signal.get("weight") == "high":
            reasons.append("当前需要重点练习")
        if not reasons:
            reasons.append("按课程顺序推进")
        queue.append({
            "id": "kp:" + kp_id,
            "title": title,
            "kp_ids": [kp_id],
            "target_count": target,
            "difficulty_mix": types or {"mixed": target},
            "reason": "；".join(reasons),
            "practice_paths": ["exam", "flash_card", "yes_no"],
            "priority": urgency + (1 - coverage),
        })
    queue.sort(key=lambda item: (-item.pop("priority"), item["id"]))
    return {
        "goals": goals,
        "queue": queue,
        "totals": {
            "target_count": sum(item["target_count"] for item in queue),
            "knowledge_points": len(queue),
            "available_minutes": minutes,
        },
        "generated_at": _iso(now),
    }


def _goal(value):
    return {
        "id": value.get("id") or value.get("goal_id") or "goal",
        "kind": value.get("kind") or "stage",
        "title": value.get("title") or "未命名目标",
        "deadline": value.get("deadline"),
    }


def _deadline_boost(goals, now):
    distances = []
    for goal in goals:
        deadline = goal.get("deadline")
        if not deadline:
            continue
        try:
            when = datetime.fromisoformat(str(deadline).replace("Z", "+00:00"))
            current = now
            if when.tzinfo and current.tzinfo is None:
                current = current.replace(tzinfo=when.tzinfo)
            distances.append(max(0, (when - current).days))
        except (TypeError, ValueError):
            continue
    if not distances:
        return 1
    days = min(distances)
    return 2 if days <= 2 else 1.5 if days <= 7 else 1


def _is_due(value, now):
    if not value:
        return False
    try:
        current = now if isinstance(now, date) and not hasattr(now, "hour") else now.date()
        return date.fromisoformat(str(value)[:10]) <= current
    except ValueError:
        return False


def _positive_int(value, fallback):
    number = _number(value, fallback)
    return max(1, int(number))


def _number(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
