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
    return errors
