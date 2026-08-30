"""Read-only SQLite projection for the mastery v0 domain experiment."""

import json


def snapshot(conn):
    """Return the evaluator's plain input rows using SELECT-only queries."""
    problems = [
        {"id": row["problem_id"], "kp_ids": json.loads(row["kp_ids"]),
         "attempts": [], "feedback": [], "schedule": None}
        for row in _rows(conn, "SELECT problem_id, kp_ids FROM problems ORDER BY problem_id")
    ]
    kps = [
        {"id": row["kp_id"], "feedback": [], "schedule": None}
        for row in _rows(conn, "SELECT kp_id FROM knowledge_points ORDER BY kp_id")
    ]
    by_problem = {item["id"]: item for item in problems}
    by_kp = {item["id"]: item for item in kps}
    for row in _rows(conn, "SELECT problem_id, status, note, created_at FROM problem_attempts ORDER BY id"):
        if row["problem_id"] in by_problem:
            by_problem[row["problem_id"]]["attempts"].append(row)
    for row in _rows(conn, "SELECT item_type, item_id, rating, note, created_at FROM feedback_events ORDER BY id"):
        owner = by_problem if row["item_type"] == "problem" else by_kp if row["item_type"] == "kp" else {}
        if row["item_id"] in owner:
            owner[row["item_id"]]["feedback"].append(row)
    for row in _rows(conn, "SELECT item_type, item_id, due_at FROM review_schedule WHERE direction='' "):
        owner = by_problem if row["item_type"] == "problem" else by_kp if row["item_type"] == "kp" else {}
        if row["item_id"] in owner:
            owner[row["item_id"]]["schedule"] = row
    return {"problems": problems, "kps": kps}


def _rows(conn, sql):
    cursor = conn.execute(sql)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
