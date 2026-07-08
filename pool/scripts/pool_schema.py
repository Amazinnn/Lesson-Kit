"""Small schema helpers shared by pool maintenance scripts."""

import sqlite3
from typing import Iterable, List


PROBLEM_STATES = ("new", "wrong", "stuck", "reviewing", "mastered")
VALID_RELATION_TYPES = (
    "prerequisite",
    "part_of",
    "contrasts",
    "generalizes",
    "variant_of",
    "applies_to",
)
VALID_RELATION_DIRECTIONS = ("directed", "symmetric")
VALID_RELATION_STRENGTHS = ("high", "medium", "low")


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


def ensure_course_network_schema(conn: sqlite3.Connection) -> List[str]:
    """Apply the course learning network relation schema idempotently."""
    changes: List[str] = []
    if not table_exists(conn, "knowledge_relations"):
        conn.execute(
            """
            CREATE TABLE knowledge_relations (
                relation_id  TEXT PRIMARY KEY,
                source_kp_id TEXT NOT NULL REFERENCES knowledge_points(kp_id),
                target_kp_id TEXT NOT NULL REFERENCES knowledge_points(kp_id),
                relation_type TEXT NOT NULL CHECK (relation_type IN (
                    'prerequisite', 'part_of', 'contrasts',
                    'generalizes', 'variant_of', 'applies_to'
                )),
                direction    TEXT NOT NULL CHECK (direction IN ('directed', 'symmetric')),
                strength     TEXT NOT NULL CHECK (strength IN ('high', 'medium', 'low')),
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
                CHECK (source_kp_id <> target_kp_id),
                UNIQUE (source_kp_id, target_kp_id, relation_type)
            )
            """
        )
        changes.append("knowledge_relations")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_relations_source "
        "ON knowledge_relations(source_kp_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_relations_target "
        "ON knowledge_relations(target_kp_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_relations_type "
        "ON knowledge_relations(relation_type)"
    )
    return changes
