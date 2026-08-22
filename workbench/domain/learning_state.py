"""Current learning-state rules without feedback-history writes."""

from datetime import date

from workbench.domain import schedule


RATING_STATE = {
    1: "needs_work", 2: "needs_work", 3: "review", 4: "review", 5: "mastered",
}
STATE_RATING = {"needs_work": 1, "review": 3, "mastered": 5}


def for_rating(rating):
    return RATING_STATE[rating]


def apply(pool, item_type, item_id, state, now=None):
    """Overwrite current state and update its ordinary review schedule."""
    rating = STATE_RATING[state]
    pool.upsert_current_state(item_type, item_id, state)
    current = pool.schedule_get(item_type, item_id) or schedule.default_state(
        item_type, item_id
    )
    next_state = schedule.after_result(current, rating, now or date.today())
    pool.schedule_upsert(next_state)
    return next_state
