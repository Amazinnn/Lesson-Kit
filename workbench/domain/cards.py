"""Flash-card content contract (pure rules).

A flash card is a derived key-value recall view over exactly one knowledge
point: the knowledge point stays the single source of truth, one card holds
one atomic fact (minimum-information discipline, enforced as content craft —
not measured here).
"""

import re

CARD_ID = re.compile(r"^[a-z0-9-]+-fc-\d{3}$")
REQUIRED_FIELDS = ("card_id", "kp_id", "front", "back", "source_evidence")
MAX_FRONT_CHARS = 100
MAX_BACK_CHARS = 300
MAX_TOPIC_LABEL_CHARS = 40
FORWARD = "forward"
REVERSE = "reverse"
DEFAULT_DIRECTIONS = [FORWARD]
BIDIRECTIONAL_DIRECTIONS = [FORWARD, REVERSE]


def is_valid_card_id(card_id):
    return isinstance(card_id, str) and bool(CARD_ID.match(card_id))


def validate_card_row(row):
    """Return contract errors; empty means the card is valid.

    Identity (id pattern, uniqueness) and knowledge-point existence are
    owned by the ingest gate; this covers the field contract only.
    """
    errors = []
    for field in REQUIRED_FIELDS:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required")
    front = row.get("front")
    if isinstance(front, str) and len(front) > MAX_FRONT_CHARS:
        errors.append(f"front exceeds {MAX_FRONT_CHARS} characters; "
                      "one card holds one atomic fact")
    back = row.get("back")
    if isinstance(back, str) and len(back) > MAX_BACK_CHARS:
        errors.append(f"back exceeds {MAX_BACK_CHARS} characters")
    if "topic_label" in row:
        topic_label = row["topic_label"]
        if not isinstance(topic_label, str) or not topic_label.strip():
            errors.append("topic_label must be a non-empty string")
        elif len(topic_label) > MAX_TOPIC_LABEL_CHARS:
            errors.append(f"topic_label exceeds {MAX_TOPIC_LABEL_CHARS} characters")
    if row.get("directions", DEFAULT_DIRECTIONS) not in (
        DEFAULT_DIRECTIONS, BIDIRECTIONAL_DIRECTIONS,
    ):
        errors.append('directions must be ["forward"] or ["forward", "reverse"]')
    return errors


def practice_directions(allowed, preference):
    """Return the concrete learning actions allowed by one session preference."""
    if preference == REVERSE:
        return [REVERSE] if REVERSE in allowed else [FORWARD]
    if preference == "mixed":
        return list(allowed)
    return [FORWARD]


def select(cards, schedule_rows, *, preference="forward", excluded_ids=(),
           excluded_directions=(), today=""):
    """Expand card rows into direction actions and order due actions first."""
    schedules = {
        (row["item_id"], row.get("direction", "")): row.get("due_at")
        for row in schedule_rows if row["item_type"] == "card"
    }
    candidates = []
    for card in cards:
        if card["card_id"] in excluded_ids:
            continue
        for direction in practice_directions(card["directions"], preference):
            if f"{card['card_id']}:{direction}" in excluded_directions:
                continue
            candidate = dict(card)
            candidate["direction"] = direction
            due_at = schedules.get((card["card_id"], direction))
            if due_at is None and direction == FORWARD:
                due_at = schedules.get((card["card_id"], ""))
            candidate["_due_at"] = str(due_at or "")
            candidates.append(candidate)
    candidates.sort(key=lambda card: (
        0 if card["_due_at"][:10] <= today and card["_due_at"] else 1,
        card["_due_at"], card["card_id"], card["direction"],
    ))
    for candidate in candidates:
        candidate.pop("_due_at")
    return candidates
