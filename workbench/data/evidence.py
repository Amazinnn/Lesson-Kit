"""Bounded, human-readable learning evidence for Agent retrieval.

This module exposes facts only. It does not infer weaknesses or summarize learner
behavior; the external Agent remains responsible for conclusions and wording.
"""

import json


DEFAULT_LIMIT = 8
MAX_LIMIT = 20


def for_kp(pool, kp_id, *, limit=DEFAULT_LIMIT):
    """Return recent attempted-problem evidence for one knowledge point.

    Rows are newest first and contain enough human-readable material to support a
    learner-facing historical claim without a second problem-id lookup. Internal
    ids remain present for provenance, but are not the evidence the learner should
    be shown.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be an integer from 1 to {MAX_LIMIT}")
    kp = pool.kp(kp_id)
    if kp is None:
        raise KeyError(kp_id)

    problems = pool.problems_for_kps([kp_id])
    by_id = {problem["problem_id"]: problem for problem in problems}
    attempts = _recent_attempts(pool, list(by_id), limit + 1)
    has_more = len(attempts) > limit
    attempts = attempts[:limit]
    feedback = _feedback_for_attempts(pool, [row["id"] for row in attempts])

    rows = [
        _evidence_row(by_id[row["problem_id"]], row, feedback.get(row["id"]))
        for row in attempts
    ]
    return {
        "knowledge_point": {
            "kp_id": kp["kp_id"],
            "knowledge_item": kp.get("knowledge_item"),
            "body": kp.get("body"),
        },
        "recent_problem_evidence": rows,
        "returned": len(rows),
        "has_more": has_more,
        "limit": limit,
    }


def _recent_attempts(pool, problem_ids, limit):
    if not problem_ids:
        return []
    placeholders = ", ".join("?" for _ in problem_ids)
    rows = pool.connect().execute(
        "SELECT * FROM problem_attempts "
        f"WHERE problem_id IN ({placeholders}) "
        "ORDER BY created_at DESC, id DESC LIMIT ?",
        (*problem_ids, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _feedback_for_attempts(pool, attempt_ids):
    if not attempt_ids:
        return {}
    conn = pool.connect()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(feedback_events)")}
    if "attempt_id" not in columns:
        return {}
    placeholders = ", ".join("?" for _ in attempt_ids)
    rows = conn.execute(
        "SELECT * FROM feedback_events "
        f"WHERE attempt_id IN ({placeholders}) ORDER BY id DESC",
        attempt_ids,
    ).fetchall()
    result = {}
    for raw in rows:
        row = dict(raw)
        result.setdefault(row["attempt_id"], row)
    return result


def _evidence_row(problem, attempt, feedback):
    raw_choices = attempt.get("choices")
    choices = None
    if isinstance(raw_choices, str) and raw_choices:
        try:
            choices = json.loads(raw_choices)
        except json.JSONDecodeError:
            choices = None
    elif isinstance(raw_choices, list):
        choices = raw_choices

    verdict = attempt.get("verdict")
    if verdict is not None:
        verdict = bool(verdict)

    return {
        "problem_id": problem["problem_id"],
        "problem_text": problem.get("problem_text"),
        "display_title": problem.get("display_title"),
        "source_kind": problem.get("source_kind"),
        "source_evidence": problem.get("source_evidence"),
        "attempt_id": attempt.get("id"),
        "status": attempt.get("status"),
        "answer_text": attempt.get("answer_text"),
        "choices": choices,
        "verdict": verdict,
        "note": attempt.get("note"),
        "created_at": attempt.get("created_at"),
        "rating": feedback.get("rating") if feedback else None,
        "feedback_note": feedback.get("note") if feedback else None,
    }
