"""Pure rules for objective problem difficulty."""

from decimal import Decimal, ROUND_HALF_UP


MODEL_ID = "cognitive-v1-equal-mean"
DIMENSIONS = (
    "knowledge_breadth",
    "reasoning_depth",
    "transfer_distance",
    "construction_openness",
)


def score(vector):
    """Validate a complete 1-5 vector and return its one-decimal mean."""
    missing = [name for name in DIMENSIONS if name not in vector]
    if missing:
        raise ValueError(f"missing dimension: {missing[0]}")
    values = [vector[name] for name in DIMENSIONS]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5
           for value in values):
        raise ValueError("each difficulty dimension must be an integer from 1 to 5")
    mean = sum(Decimal(value) for value in values) / Decimal(len(values))
    return mean.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def band(value):
    """Project a stored total to its nearest 1-5 band, half up."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
