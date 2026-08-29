"""Problem pull engine (pure rules over a Pool)."""

import random

PRACTICE_MODES = {"exam", "micro", "yes_no"}


def select(pool, kp_ids, n, mode="weak", source_kind=None, exclude_ids=None,
           seed=None, include_ids=None):
    """Pull durable problems and report gaps.

    Never fabricates content: whatever cannot be filled is listed in
    ``shortage``. Candidate staging is retired (2026-08-29 Check pipeline):
    the pull engine reads formal problems only. ``include_ids`` optionally
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
    if include_ids:
        problems = [p for p in problems if p["problem_id"] in include_ids]
    problems = [p for p in problems if p["problem_id"] not in exclude_ids]

    shortage = []
    if order_mode != "all":
        for kp_id in kp_ids:
            durable = sum(1 for p in problems if kp_id in p["kp_ids"])
            if durable < n:
                shortage.append(kp_id)

    return {
        "problems": problems[:n],
        "candidates": [],
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
