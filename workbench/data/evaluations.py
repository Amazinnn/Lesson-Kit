"""Evaluation records: list/get/add/update/delete for the Agent CLI.

An evaluation is one ``feedback_events`` row. Update and delete are in-place and
do not replay learning projections; ``attempts correct`` remains the whole-attempt
replacement path that withdraws and recomputes the linked effects.
"""

from workbench.data import attempts as attempt_records
from workbench.domain import feedback as feedback_rules

UNSET = object()
MAX_LIMIT = 500
ITEM_TYPES = ("kp", "problem", "card")


class EvaluationError(ValueError):
    pass


class EvaluationConflict(EvaluationError):
    pass


class EvaluationDuplicate(EvaluationConflict):
    def __init__(self, message, event_id):
        super().__init__(message)
        self.event_id = event_id


def _event(pool, event_id):
    if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id <= 0:
        raise EvaluationError("event_id must be a positive integer")
    event = pool.feedback_event(event_id)
    if event is None:
        raise EvaluationError(f"unknown evaluation: {event_id}")
    return event


def _rating(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value not in range(1, 6):
        raise EvaluationError("rating must be an integer from 1 to 5")
    return value


def _note(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise EvaluationError("note must be a string")
    return value if value.strip() else None


def _expected(event, expected_rating, expected_note):
    if expected_rating != event["rating"]:
        raise EvaluationConflict(
            f"evaluation {event['id']} has rating {event['rating']!r}, "
            f"not {expected_rating!r}; read it again")
    if (expected_note or "") != (event["note"] or ""):
        raise EvaluationConflict(
            f"evaluation {event['id']} has a different note; read it again")


def _agent_recorded(pool, event):
    attempt_id = event.get("attempt_id")
    return bool(attempt_id and attempt_records.linked_operation(pool, attempt_id))


def _correctable(pool, event):
    attempt_id = event.get("attempt_id")
    if not attempt_id:
        return False
    operation = attempt_records.linked_operation(pool, attempt_id)
    attempt = pool.attempt(attempt_id)
    if operation is None or attempt is None:
        return False
    return attempt_records.correction_conflict(pool, attempt, operation) is None


def _serialize(pool, event):
    return {
        "event_id": event["id"],
        "item_type": event["item_type"],
        "item_id": event["item_id"],
        "rating": event["rating"],
        "note": event["note"],
        "attempt_id": event.get("attempt_id"),
        "created_at": event["created_at"],
        "agent_recorded": _agent_recorded(pool, event),
        "correctable": _correctable(pool, event),
    }


def list_events(pool, item_type=None, item_id=None, attempt_id=None, limit=50):
    if item_type is not None and item_type not in ITEM_TYPES:
        raise EvaluationError("item_type must be kp, problem, or card")
    if (item_type is None) != (item_id is None):
        raise EvaluationError("--item and --id must be used together")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise EvaluationError(f"limit must be between 1 and {MAX_LIMIT}")
    rows = pool.feedback_event_rows(
        item_type=item_type, item_id=item_id, attempt_id=attempt_id, limit=limit)
    return {"count": len(rows), "events": [_serialize(pool, row) for row in rows]}


def get_event(pool, event_id):
    return _serialize(pool, _event(pool, event_id))


def add_event(pool, item_type, item_id, rating=None, note=None, direction="",
              attempt_id=None):
    if item_type not in ITEM_TYPES:
        raise EvaluationError("item_type must be kp, problem, or card")
    lookup = {"kp": pool.kp, "problem": pool.problem, "card": pool.card}[item_type]
    item = lookup(item_id)
    if item is None:
        raise EvaluationError(f"unknown {item_type}: {item_id}")
    direction = direction or ""
    if item_type == "card" and direction not in {"", *item["directions"]}:
        raise EvaluationError("direction is not available for this card")
    rating = _rating(rating)
    note = _note(note)
    if rating is None and note is None:
        raise EvaluationError("rating or note is required")
    if attempt_id is not None:
        if item_type != "problem":
            raise EvaluationError("--attempt-id applies only to problem evaluations")
        attempt = pool.attempt(attempt_id)
        if attempt is None:
            raise EvaluationError(f"unknown attempt: {attempt_id}")
        if attempt["problem_id"] != item_id:
            raise EvaluationError(
                f"attempt {attempt_id} does not belong to {item_id}")
        existing = pool.feedback_event_for_attempt(attempt_id)
        if existing is not None:
            raise EvaluationDuplicate(
                f"attempt {attempt_id} already has evaluation {existing['id']}; "
                "use feedback update", existing["id"])
    changes = feedback_rules.apply(
        pool, item_type, item_id, rating=rating, note=note,
        direction=direction, attempt_id=attempt_id)
    if attempt_id is not None:
        event = pool.feedback_event_for_attempt(attempt_id)
    else:
        event = pool.feedback_events(item_type, item_id)[-1]
    if event is None:
        raise EvaluationError("evaluation was not recorded")
    return {"event": _serialize(pool, event), "changes": changes}


def update_event(pool, event_id, rating=UNSET, note=UNSET, *,
                 expected_rating, expected_note):
    event = _event(pool, event_id)
    _expected(event, expected_rating, expected_note)
    if rating is UNSET and note is UNSET:
        raise EvaluationError("update requires --rating or --note")
    next_rating = event["rating"] if rating is UNSET else _rating(rating)
    next_note = event["note"] if note is UNSET else _note(note)
    if next_rating is None and next_note is None:
        raise EvaluationError(
            "an evaluation must keep a rating or a note; delete it instead")
    pool.update_feedback_event(event_id, next_rating, next_note)
    return _serialize(pool, pool.feedback_event(event_id))


def delete_event(pool, event_id, *, expected_rating, expected_note):
    event = _event(pool, event_id)
    _expected(event, expected_rating, expected_note)
    pool.delete_feedback_event(event_id)
    return {"deleted": True, "event_id": event_id}
