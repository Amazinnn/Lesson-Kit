"""Pure deterministic aggregation for current learner signals."""

WEIGHT_RANK = {"low": 0, "medium": 1, "high": 2}


def strongest_by_target(rows, target_type="node"):
    """Return one stable strongest signal per target without double counting."""
    grouped = {}
    for row in rows or []:
        if row.get("target_type", "node") != target_type:
            continue
        target_id = row.get("target_id")
        if not target_id:
            continue
        grouped.setdefault(target_id, []).append(row)
    return {
        target_id: min(items, key=_priority)
        for target_id, items in grouped.items()
    }


def _priority(row):
    """Strongest weight, then evidence, then a stable lexical identity."""
    identity = row.get("signal_id") or row.get("signal_type") or ""
    return (
        -WEIGHT_RANK.get(row.get("weight"), 1),
        -_evidence(row.get("evidence_count")),
        identity,
    )


def _evidence(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
