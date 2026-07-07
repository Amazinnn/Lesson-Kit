"""Small schema helpers shared by pool maintenance scripts."""

import sqlite3
from typing import Iterable, List


PROBLEM_STATES = ("new", "wrong", "stuck", "reviewing", "mastered")


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def column_names(conn: sqlite3.Connection, table: str) -> List[str]:
    if not table_exists(conn, table):
        return []
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")]


def ensure_columns(
    conn: sqlite3.Connection,
    table: str,
    columns: Iterable[tuple[str, str]],
) -> List[str]:
    existing = set(column_names(conn, table))
    added: List[str] = []
    for name, ddl in columns:
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
            added.append(f"{table}.{name}")
    return added


def ensure_learning_state_schema(conn: sqlite3.Connection) -> List[str]:
    """Apply the lightweight learning-state schema migration idempotently."""
    changes: List[str] = []
    if table_exists(conn, "knowledge_points"):
        changes.extend(
            ensure_columns(
                conn,
                "knowledge_points",
                [("graph_label", "TEXT")],
            )
        )

    if not table_exists(conn, "problem_progress"):
        conn.execute(
            """
            CREATE TABLE problem_progress (
                problem_id TEXT PRIMARY KEY REFERENCES problems(problem_id),
                status     TEXT NOT NULL DEFAULT 'new'
                           CHECK (status IN (
                               'new', 'wrong', 'stuck', 'reviewing', 'mastered'
                           )),
                note       TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("problem_progress")
    else:
        changes.extend(
            ensure_columns(
                conn,
                "problem_progress",
                [
                    ("status", "TEXT NOT NULL DEFAULT 'new'"),
                    ("note", "TEXT"),
                    ("updated_at", "TEXT"),
                ],
            )
        )
        conn.execute(
            "UPDATE problem_progress SET updated_at = datetime('now') "
            "WHERE updated_at IS NULL"
        )

    if not table_exists(conn, "problem_attempts"):
        conn.execute(
            """
            CREATE TABLE problem_attempts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL REFERENCES problems(problem_id),
                status     TEXT NOT NULL
                           CHECK (status IN (
                               'new', 'wrong', 'stuck', 'reviewing', 'mastered'
                           )),
                note       TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("problem_attempts")
    else:
        changes.extend(
            ensure_columns(
                conn,
                "problem_attempts",
                [
                    ("problem_id", "TEXT"),
                    ("status", "TEXT"),
                    ("note", "TEXT"),
                    ("created_at", "TEXT"),
                ],
            )
        )
        conn.execute(
            "UPDATE problem_attempts SET created_at = datetime('now') "
            "WHERE created_at IS NULL"
        )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_problem_progress_status "
        "ON problem_progress(status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_problem_attempts_problem_id "
        "ON problem_attempts(problem_id)"
    )
    return changes
