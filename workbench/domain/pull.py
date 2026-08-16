"""Problem pull engine (pure rules over a Pool)."""

import random


def select(pool, kp_ids, n, mode="weak", source_kind=None, exclude_ids=None,
           seed=None):
    """Pull durable problems, then gate-passed candidates, then report gaps.

    Never fabricates content: whatever cannot be filled is listed in
    ``shortage``.
    """
    exclude_ids = exclude_ids or set()
    if mode == "all":
        problems = pool.problems_all()
        if source_kind:
            problems = [p for p in problems if p["source_kind"] == source_kind]
    else:
        problems = pool.problems_for_kps(kp_ids, source_kind)
        if mode == "weak":
            problems = sorted(
                problems,
                key=lambda p: (-_hit_count(p, kp_ids), p["problem_id"]),
            )
        elif mode == "random":
            random.Random(seed).shuffle(problems)
    problems = [p for p in problems if p["problem_id"] not in exclude_ids]

    candidates = []
    if len(problems) < n and mode != "all":
        candidates = [
            c for c in pool.gate_passed_candidates(kp_ids)
            if c["candidate_id"] not in exclude_ids
        ]
        candidates = sorted(
            candidates,
            key=lambda c: (-_hit_count(c, kp_ids), c["candidate_id"]),
        )

    shortage = []
    if mode != "all":
        for kp_id in kp_ids:
            durable = sum(1 for p in problems if kp_id in p["kp_ids"])
            extra = sum(1 for c in candidates if kp_id in c["kp_ids"])
            if durable + extra < n:
                shortage.append(kp_id)

    return {
        "problems": problems[:n],
        "candidates": candidates[: max(0, n - len(problems))],
        "shortage": shortage,
    }


def _hit_count(item, kp_ids):
    return sum(1 for kp_id in kp_ids if kp_id in item["kp_ids"])
