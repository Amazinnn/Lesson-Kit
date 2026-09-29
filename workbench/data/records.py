"""Read-only practice-record queries."""

import json
import sqlite3
from datetime import date, timedelta

from workbench.data import active_practice


def _tables(conn):
    return {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def _run_summary(record, *, run_id=None, status=None, finished_at=None):
    items = record.get("items") or []
    answered = sum(item.get("state") == "answered" for item in items)
    stuck = sum(item.get("state") == "stuck" for item in items)
    return {
        "run_id": run_id,
        "source_kind": record.get("source_kind") or "quick",
        "source_ref": record.get("source_ref"),
        "source_label": record.get("source_label") or (
            f"试卷 {record.get('source_ref')}" if record.get("source_kind") == "practice_set"
            and record.get("source_ref") else "临时练习"
        ),
        "practice_mode": record.get("practice_mode"),
        "rating_mode": record.get("rating_mode"),
        "started_at": record.get("started_at"),
        "finished_at": finished_at,
        "status": status or "active",
        "progress": {
            "completed": answered + stuck,
            "answered": answered,
            "stuck": stuck,
            "remaining": len(items) - answered - stuck,
            "total": len(items),
        },
    }


def _runs(pool, limit):
    conn = pool.connect()
    if "practice_runs" not in _tables(conn):
        return None, []
    active = active_practice.current(pool, resolve=False)
    active_record = _run_summary(active) if active else None
    rows = conn.execute(
        "SELECT * FROM practice_runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    history = []
    for row in rows:
        record = dict(row)
        record["items"] = json.loads(record.pop("items_json") or "[]")
        record["kp_ids"] = json.loads(record.pop("kp_ids_json") or "[]")
        history.append(_run_summary(
            record,
            run_id=record["id"],
            status=record["status"],
            finished_at=record["finished_at"],
        ))
    return active_record, history


def _summary(conn, problem_id, verdict_column, linked_feedback):
    where = " WHERE problem_id=?" if problem_id else ""
    params = [problem_id] if problem_id else []
    total = conn.execute(
        "SELECT COUNT(*) FROM problem_attempts" + where, params
    ).fetchone()[0]
    judged = correct = 0
    if verdict_column:
        judged, correct = conn.execute(
            "SELECT COUNT(verdict), COALESCE(SUM(verdict = 1), 0) "
            "FROM problem_attempts" + where,
            params,
        ).fetchone()
    rated = 0
    average_rating = None
    if linked_feedback:
        rating_where = " WHERE a.problem_id=?" if problem_id else ""
        rated, average_rating = conn.execute(
            "SELECT COUNT(f.rating), AVG(f.rating) "
            "FROM feedback_events f JOIN problem_attempts a ON a.id=f.attempt_id"
            + rating_where,
            params,
        ).fetchone()
    return {
        "attempts": total,
        "judged": judged,
        "correct": correct,
        "accuracy": (correct / judged) if judged else None,
        "rated": rated,
        "average_rating": average_rating,
    }


def _trend(conn, problem_id, verdict_column, days=14):
    first = date.today() - timedelta(days=days - 1)
    params = [first.isoformat()]
    where = "created_at >= ?"
    if problem_id:
        where += " AND problem_id=?"
        params.append(problem_id)
    verdict_sql = (
        ", COALESCE(SUM(verdict = 1), 0) AS correct,"
        " COALESCE(SUM(verdict = 0), 0) AS wrong"
        if verdict_column else ", 0 AS correct, 0 AS wrong"
    )
    rows = {
        row["day"]: dict(row)
        for row in conn.execute(
            "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS attempts"
            + verdict_sql
            + " FROM problem_attempts WHERE " + where
            + " GROUP BY substr(created_at, 1, 10)",
            params,
        )
    }
    return [
        {
            "date": (first + timedelta(days=offset)).isoformat(),
            "attempts": rows.get(
                (first + timedelta(days=offset)).isoformat(), {}
            ).get("attempts", 0),
            "correct": rows.get(
                (first + timedelta(days=offset)).isoformat(), {}
            ).get("correct", 0),
            "wrong": rows.get(
                (first + timedelta(days=offset)).isoformat(), {}
            ).get("wrong", 0),
        }
        for offset in range(days)
    ]


def _rating_distribution(conn, problem_id, linked_feedback):
    counts = {rating: 0 for rating in range(1, 6)}
    if not linked_feedback:
        return [{"rating": rating, "count": 0} for rating in counts]
    where = " WHERE a.problem_id=?" if problem_id else ""
    params = [problem_id] if problem_id else []
    for row in conn.execute(
        "SELECT f.rating, COUNT(*) AS count "
        "FROM feedback_events f JOIN problem_attempts a ON a.id=f.attempt_id"
        + where + " GROUP BY f.rating",
        params,
    ):
        if row["rating"] in counts:
            counts[row["rating"]] = row["count"]
    return [{"rating": rating, "count": counts[rating]} for rating in counts]


def overview(pool, limit=100, problem_id=None):
    """Return attempts plus the small derived views used by the records page."""
    conn = pool.connect()
    conn.row_factory = sqlite3.Row
    titles = {row["problem_id"]: row for row in conn.execute("SELECT * FROM problems")}
    where = ""
    params = []
    if problem_id:
        where = " WHERE a.problem_id=?"
        params.append(problem_id)
    feedback_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(feedback_events)")
    }
    attempt_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(problem_attempts)")
    }
    linked = "attempt_id" in feedback_columns
    has_verdict = "verdict" in attempt_columns
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
            "verdict": row["verdict"] if has_verdict else None,
            "choices": (
                json.loads(row["choices"])
                if "choices" in row.keys() and row["choices"] else None
            ),
            "answer_text": row["answer_text"],
            "note": row["note"],
            "rating": mark["rating"] if mark else None,
            "feedback_note": mark["note"] if mark else None,
            "created_at": row["created_at"],
        })
    active_run, runs = _runs(pool, limit)
    return {
        "count": len(records),
        "records": records,
        "summary": _summary(conn, problem_id, has_verdict, linked),
        "trend": _trend(conn, problem_id, has_verdict),
        "ratings": _rating_distribution(conn, problem_id, linked),
        "active_run": active_run,
        "runs": runs,
    }
