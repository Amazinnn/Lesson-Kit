"""Feedback mapping: ratings and natural-language notes to signals/events."""

from datetime import date

from workbench.domain import learning_state
from workbench.domain import schedule as schedule_rules

KEYWORD_RULES = [
    (("混淆", "分不清", "区别", "搞混", "相似"), "confusion"),
    (("前置", "没学", "基础", "缺"), "missing_prerequisite"),
    (("别的章节", "用不上", "迁移"), "transfer_failure"),
    (("缺联系", "关系", "连不上", "联系不上"), "relation_gap"),
]
DEFAULT_SIGNAL_TYPE = "weak_node"
RATING_WEIGHT = {1: "high", 2: "high", 3: "medium", 4: "low", 5: None}
RATING_PROGRESS = {1: "wrong", 2: "wrong", 3: "reviewing", 4: "reviewing", 5: "mastered"}


def apply(pool, item_type, item_id, rating=None, note=None, direction=""):
    """Record feedback and update signals, events, progress, and schedule.

    ``direction`` selects the schedule row key (default "" = forward); it does
    not change progress, current-state, or signal semantics.
    Returns a list of human-readable changes for the UI.
    """
    changes = []
    targets = _targets(pool, item_type, item_id)
    signal_type = _signal_type(note)

    for target_id in targets:
        existing = next(
            (s for s in pool.signals() if s["target_id"] == target_id), None
        )
        weight = RATING_WEIGHT.get(rating) if rating is not None else None
        if weight is not None:
            evidence = (existing["evidence_count"] + 1) if existing else 1
            pool.upsert_signal("node", target_id, signal_type, weight, evidence, note)
            changes.append(f"signal {target_id}: {weight} ({evidence}x)")
        elif rating is not None:
            if existing:
                pool.upsert_signal(
                    "node", target_id, existing["signal_type"],
                    existing["weight"], existing["evidence_count"] + 1, note,
                )
                changes.append(f"signal {target_id}: evidence+1, weight kept")
        elif note:
            evidence = (existing["evidence_count"] + 1) if existing else 1
            keep_weight = existing["weight"] if existing else "medium"
            pool.upsert_signal(
                "node", target_id, signal_type, keep_weight, evidence, note,
            )
            changes.append(f"signal {target_id}: {signal_type}, note saved")

    if rating is not None or note:
        pool.insert_feedback_event(item_type, item_id, rating, note)
        changes.append("event logged")

    if item_type == "problem" and rating is not None:
        progress = RATING_PROGRESS[rating]
        pool.upsert_problem_progress(item_id, progress, note)
        pool.upsert_current_state("problem", item_id, learning_state.for_rating(rating))
        changes.append(f"progress: {progress}")

    if rating is not None:
        for target_id in targets:
            pool.upsert_current_state("kp", target_id, learning_state.for_rating(rating))

    if rating is not None:
        state = pool.schedule_get(item_type, item_id, direction) or \
            schedule_rules.default_state(item_type, item_id, direction)
        next_state = schedule_rules.after_result(state, rating, date.today())
        pool.schedule_upsert(next_state)
        changes.append(f"schedule: due {next_state['due_at']}")

    return changes


def _targets(pool, item_type, item_id):
    if item_type == "problem":
        problem = pool.problem(item_id)
        return problem["kp_ids"] if problem else []
    return [item_id]


def _signal_type(note):
    if not note:
        return DEFAULT_SIGNAL_TYPE
    for keywords, signal_type in KEYWORD_RULES:
        if any(keyword in note for keyword in keywords):
            return signal_type
    return DEFAULT_SIGNAL_TYPE
