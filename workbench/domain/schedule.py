"""SM-2 variant scheduling rules (pure)."""

from datetime import date, timedelta

EASE_FLOOR = 1.3
EASE_CAP = 3.0
EASE_UP = 0.1
EASE_DOWN = 0.2

RESULT_QUALITY = {"correct": 4, "wrong": 2, "stuck": 2, "skip": None}


def after_result(state, result, now):
    """Return the next schedule state after a practice result or rating.

    result is 'correct' | 'wrong' | 'stuck' | 'skip' or an int rating 1-5.
    'skip' (no time to grade) leaves the schedule unchanged.
    """
    q = result if isinstance(result, int) else RESULT_QUALITY.get(result)
    if q is None:
        return dict(state)

    next_state = dict(state)
    if q < 3:
        next_state["repetitions"] = 0
        next_state["interval_days"] = 0.0
        next_state["ease"] = max(EASE_FLOOR, next_state["ease"] - EASE_DOWN)
        next_state["state"] = "relearning"
    else:
        next_state["repetitions"] = next_state["repetitions"] + 1
        if next_state["repetitions"] == 1:
            next_state["interval_days"] = 1.0
        elif next_state["repetitions"] == 2:
            next_state["interval_days"] = 6.0
        else:
            next_state["interval_days"] = round(
                next_state["interval_days"] * next_state["ease"]
            )
        next_state["ease"] = min(EASE_CAP, next_state["ease"] + EASE_UP)
        next_state["state"] = "review"

    next_state["last_rating"] = q
    next_state["due_at"] = (now + timedelta(days=next_state["interval_days"])).isoformat()
    next_state["last_reviewed_at"] = now.isoformat()
    return next_state


def default_state(item_type, item_id, direction=""):
    return {
        "item_type": item_type,
        "item_id": item_id,
        "direction": direction,
        "state": "learning",
        "repetitions": 0,
        "ease": 2.5,
        "interval_days": 0.0,
        "due_at": None,
        "last_rating": None,
        "last_reviewed_at": None,
    }
