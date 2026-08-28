"""Pure, deterministic rules for a coarse daily learning plan."""

from datetime import date, datetime
import copy
import math

DEFAULT_TARGET = 3


def build_baseline_plan(workspace, *, now=None, available_minutes=None):
    """Build a truthful, at-most-three-item plan from Data-layer facts."""
    now = now or datetime.now()
    facts = workspace or {}
    kps = list(facts.get("kps") or [])
    problems = list(facts.get("problems") or [])
    progress = facts.get("progress") or {}
    signals = {row.get("target_id"): row for row in facts.get("signals") or []}
    due = {
        row.get("item_id") for row in facts.get("schedule") or []
        if row.get("item_type") == "kp" and _is_due(row.get("due_at"), now)
    }
    goals = [_goal(row) for row in facts.get("goals") or [] if isinstance(row, dict)]
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
        urgency = 3 if signal.get("weight") == "high" else 2 if signal.get("weight") == "medium" else 0
        if kp_id in due:
            urgency += 2
        if kp.get("importance") == "core":
            urgency += 1
        target = DEFAULT_TARGET + (1 if coverage < 0.5 else 0) + (1 if urgency >= 3 else 0)
        if deadline_boost > 1:
            target += math.ceil(deadline_boost - 1)
        target = max(1, min(target, len(linked))) if linked else 1
        reasons = []
        if coverage < 0.5:
            reasons.append("覆盖仍低")
        if kp_id in due:
            reasons.append("复习已到期")
        if signal.get("weight") == "high":
            reasons.append("当前需要重点练习")
        if not reasons:
            reasons.append("按课程顺序推进")
        types = {}
        for problem in linked:
            kind = problem.get("problem_type") or "other"
            types[kind] = types.get(kind, 0) + 1
        queue.append({
            "id": "kp:" + kp_id,
            "title": kp.get("knowledge_item") or kp_id,
            "kp_ids": [kp_id],
            "target_count": target,
            "difficulty_mix": types or {"mixed": target},
            "reason": "；".join(reasons),
            "priority": urgency + (1 - coverage),
        })
    queue.sort(key=lambda item: (-item.pop("priority"), item["id"]))
    queue = queue[:3]
    totals = {
        "target_count": sum(item["target_count"] for item in queue),
        "knowledge_points": len(queue),
    }
    if available_minutes is not None:
        totals["available_minutes"] = _positive_int(available_minutes, 45)
    return {"goals": goals, "queue": queue, "totals": totals, "generated_at": _iso(now)}


def apply_adjustment(plan, adjustment):
    """Apply the existing bounded Agent adjustment contract."""
    if not isinstance(adjustment, dict):
        return plan
    result = copy.deepcopy(plan)
    queue = result.get("queue") or []
    if isinstance(adjustment.get("queue"), list):
        updates = {item.get("id"): item for item in adjustment["queue"] if isinstance(item, dict)}
        for item in queue:
            change = updates.get(item.get("id"))
            if change and isinstance(change.get("target_count"), (int, float)):
                item["target_count"] = max(1, min(20, int(change["target_count"])))
    elif isinstance(adjustment.get("target_count"), (int, float)):
        target = max(1, min(20, int(adjustment["target_count"])))
        for item in queue:
            item["target_count"] = target
    result.setdefault("totals", {})["target_count"] = sum(item.get("target_count", 0) for item in queue)
    result["adjusted"] = True
    return result


def _goal(value):
    return {
        "id": value.get("id") or value.get("goal_id") or "goal",
        "kind": value.get("kind") or "stage",
        "title": value.get("title") or "未命名目标",
        "deadline": value.get("deadline"),
        "progress": value.get("progress"),
        "coverage_progress": value.get("coverage_progress"),
        "description": value.get("description"),
        "scope": value.get("scope"),
    }


def _deadline_boost(goals, now):
    distances = []
    for goal in goals:
        if not goal.get("deadline"):
            continue
        try:
            when = datetime.fromisoformat(str(goal["deadline"]).replace("Z", "+00:00"))
            current = now.replace(tzinfo=when.tzinfo) if when.tzinfo and now.tzinfo is None else now
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
    return max(1, int(_number(value, fallback)))


def _number(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
