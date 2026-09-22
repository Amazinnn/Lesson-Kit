"""Problem pull engine (pure rules over a Pool)."""

from decimal import Decimal, ROUND_HALF_UP
import random

PRACTICE_MODES = {"exam", "micro", "yes_no"}


def select(pool, kp_ids, n, mode="weak", source_kind=None, origin_kind=None,
           source_group=None, exclude_ids=None, seed=None, include_ids=None,
           difficulty_min=None, difficulty_max=None, difficulty_dimensions=None,
           difficulty_strategy=None):
    """Pull durable problems and report gaps.

    Never fabricates content: whatever cannot be filled is listed in
    ``shortage``. The pull engine reads formal problems only. ``include_ids`` optionally
    restricts the result to those identifiers within the requested scope.
    """
    exclude_ids = exclude_ids or set()
    include_ids = set(include_ids or [])
    practice_mode = mode if mode in PRACTICE_MODES else None
    order_mode = "weak" if practice_mode else mode
    if order_mode == "all":
        problems = pool.problems_all()
        if source_kind:
            problems = [p for p in problems if p["source_kind"] == source_kind]
    else:
        problems = pool.problems_for_kps(kp_ids, source_kind)
        if order_mode == "weak":
            problems = sorted(
                problems,
                key=lambda p: (-_hit_count(p, kp_ids), p["problem_id"]),
            )
        elif order_mode == "random":
            random.Random(seed).shuffle(problems)
    if practice_mode:
        problems = [p for p in problems if _eligible_for_mode(p, practice_mode)]
    if origin_kind:
        problems = [p for p in problems if p.get("origin_kind") == origin_kind]
    if source_group:
        problems = [p for p in problems if _source_group(p) == source_group]
    if difficulty_min is not None or difficulty_max is not None or difficulty_dimensions:
        problems = [
            p for p in problems
            if _matches_difficulty(
                p, difficulty_min, difficulty_max, difficulty_dimensions or {}
            )
        ]
    if include_ids:
        problems = [p for p in problems if p["problem_id"] in include_ids]
    problems = [p for p in problems if p["problem_id"] not in exclude_ids]
    if difficulty_strategy == "balanced":
        problems = _balanced(problems)

    shortage = []
    if order_mode != "all":
        for kp_id in kp_ids:
            durable = sum(1 for p in problems if kp_id in p["kp_ids"])
            if durable < n:
                shortage.append(kp_id)

    return {
        "problems": problems[:n],
        "shortage": shortage,
    }


def _hit_count(item, kp_ids):
    return sum(1 for kp_id in kp_ids if kp_id in item["kp_ids"])


def _eligible_for_mode(item, mode):
    """Unmarked durable content is exam-only; other modes are explicit."""
    declared = item.get("practice_modes", item.get("practice_mode"))
    if isinstance(declared, str):
        declared = [declared]
    declared = set(declared or [])
    return mode in declared if declared else mode == "exam"


def _source_group(item):
    if item.get("origin_kind") == "generated_grounded":
        return "ai_generated"
    source = item.get("source_kind")
    if source == "textbook":
        return "textbook"
    if source in {"quiz", "midterm", "final", "makeup"}:
        return "exam"
    return "other"


def _matches_difficulty(item, minimum, maximum, dimension_ranges):
    total = item.get("difficulty")
    if total is None:
        return False
    if minimum is not None and total < minimum:
        return False
    if maximum is not None and total > maximum:
        return False
    for dimension, bounds in dimension_ranges.items():
        value = item.get("difficulty_" + dimension)
        low, high = bounds
        if value is None or (low is not None and value < low) or (
            high is not None and value > high
        ):
            return False
    return True


def _balanced(problems):
    buckets = {band: [] for band in range(1, 6)}
    unrated = []
    for problem in problems:
        value = problem.get("difficulty")
        if value is None:
            unrated.append(problem)
            continue
        band = int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        buckets[band].append(problem)
    ordered = []
    while any(buckets.values()):
        for band in (3, 2, 4, 1, 5):
            if buckets[band]:
                ordered.append(buckets[band].pop(0))
    return ordered + unrated
