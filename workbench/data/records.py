"""Read-only practice-record queries."""

import json
import sqlite3


def overview(pool, limit=100, problem_id=None):
    """Return practice attempts newest first across the course."""
    conn = pool.connect()
    conn.row_factory = sqlite3.Row
    titles = {row["problem_id"]: row for row in conn.execute("SELECT * FROM problems")}
    where = ""
    params = []
    if problem_id:
        where = " WHERE a.problem_id=?"
        params.append(problem_id)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(feedback_events)")}
    linked = "attempt_id" in columns
    rows = conn.execute(
        "SELECT a.* FROM problem_attempts a" + where +
        " ORDER BY a.id DESC LIMIT ?", [*params, limit]).fetchall()
    ratings = {}
    if linked and rows:
        marks = ",".join(["?"] * len(rows))
        for row in conn.execute(
            "SELECT attempt_id, rating, note FROM feedback_events"
            f" WHERE attempt_id IN ({marks})",
            [row["id"] for row in rows],
        ):
            ratings[row["attempt_id"]] = row
    records = []
    for row in rows:
        problem = titles.get(row["problem_id"])
        mark = ratings.get(row["id"])
        problem = dict(problem) if problem is not None else {}
        records.append({
            "attempt_id": row["id"],
            "problem_id": row["problem_id"],
            "title": problem.get("display_title")
            or problem.get("problem_text", "")[:60],
            "kp_ids": json.loads(problem.get("kp_ids") or "[]"),
            "status": row["status"],
            "verdict": row["verdict"] if "verdict" in row.keys() else None,
            "choices": (json.loads(row["choices"])
                        if "choices" in row.keys() and row["choices"] else None),
            "answer_text": row["answer_text"],
            "note": row["note"],
            "rating": mark["rating"] if mark else None,
            "feedback_note": mark["note"] if mark else None,
            "created_at": row["created_at"],
        })
    return {"count": len(records), "records": records}
