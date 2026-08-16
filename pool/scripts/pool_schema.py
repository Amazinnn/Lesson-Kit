"""Small schema helpers shared by pool maintenance scripts."""

import sqlite3
from typing import Iterable, List


PROBLEM_STATES = ("new", "wrong", "stuck", "reviewing", "mastered")
CANDIDATE_STATUSES = (
    "draft",
    "gate_passed",
    "needs_revision",
    "rejected",
    "imported",
)
GATE_STATUSES = ("pending", "pass", "fail")
INTERACTION_TYPES = ("single_choice", "true_false", "free_response")
GENERATION_PURPOSES = ("first_pass_check", "remediation")
ORIGIN_KINDS = ("source_problem", "adapted_problem", "generated_grounded")
SIGNAL_TYPES = (
    "weak_node",
    "confusion",
    "missing_prerequisite",
    "transfer_failure",
    "relation_gap",
)
SIGNAL_WEIGHTS = ("low", "medium", "high")
SIGNAL_TARGET_TYPES = ("node", "relation")
PRACTICE_KINDS = ("candidate", "problem", "reflection", "other")
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


def ensure_problem_candidate_schema(conn: sqlite3.Connection) -> List[str]:
    """Apply the Problem Candidate and learner-signal schema idempotently."""
    changes: List[str] = []
    if not table_exists(conn, "candidate_problems"):
        conn.execute(
            """
            CREATE TABLE candidate_problems (
                candidate_id         TEXT PRIMARY KEY,
                kp_ids               TEXT NOT NULL,
                problem_text         TEXT NOT NULL,
                options_json         TEXT,
                correct_option_id    TEXT,
                solution             TEXT,
                problem_type         TEXT NOT NULL CHECK (problem_type IN (
                    'calculation', 'proof', 'modeling', 'explanation',
                    'experiment', 'design', 'application',
                    'counterexample', 'other'
                )),
                interaction_type     TEXT NOT NULL CHECK (interaction_type IN (
                    'single_choice', 'true_false', 'free_response'
                )),
                generation_purpose   TEXT NOT NULL CHECK (generation_purpose IN (
                    'first_pass_check', 'remediation'
                )),
                origin_kind          TEXT NOT NULL CHECK (origin_kind IN (
                    'source_problem', 'adapted_problem', 'generated_grounded'
                )),
                source_kind          TEXT NOT NULL CHECK (source_kind IN (
                    'textbook', 'quiz', 'midterm', 'final', 'makeup', 'other'
                )),
                source_evidence_json TEXT NOT NULL,
                status               TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
                    'draft', 'gate_passed', 'needs_revision', 'rejected', 'imported'
                )),
                structure_gate_status TEXT NOT NULL DEFAULT 'pending' CHECK (
                    structure_gate_status IN ('pending', 'pass', 'fail')
                ),
                audit_gate_status    TEXT NOT NULL DEFAULT 'pending' CHECK (
                    audit_gate_status IN ('pending', 'pass', 'fail')
                ),
                gate_report          TEXT,
                imported_problem_id  TEXT UNIQUE REFERENCES problems(problem_id),
                created_at           TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("candidate_problems")

    if not table_exists(conn, "candidate_attempts"):
        conn.execute(
            """
            CREATE TABLE candidate_attempts (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id       TEXT NOT NULL REFERENCES candidate_problems(candidate_id),
                status             TEXT NOT NULL CHECK (status IN (
                    'new', 'wrong', 'stuck', 'reviewing', 'mastered'
                )),
                selected_option_id TEXT,
                is_correct         INTEGER CHECK (is_correct IN (0, 1)),
                note               TEXT,
                created_at         TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("candidate_attempts")

    if not table_exists(conn, "learner_signals"):
        conn.execute(
            """
            CREATE TABLE learner_signals (
                signal_id          TEXT PRIMARY KEY,
                target_type        TEXT NOT NULL CHECK (target_type IN ('node', 'relation')),
                target_id          TEXT NOT NULL,
                signal_type        TEXT NOT NULL CHECK (signal_type IN (
                    'weak_node', 'confusion', 'missing_prerequisite',
                    'transfer_failure', 'relation_gap'
                )),
                weight             TEXT NOT NULL DEFAULT 'medium' CHECK (
                    weight IN ('low', 'medium', 'high')
                ),
                evidence_count     INTEGER NOT NULL DEFAULT 1 CHECK (evidence_count >= 1),
                note               TEXT,
                last_practice_kind TEXT NOT NULL DEFAULT 'other' CHECK (
                    last_practice_kind IN ('candidate', 'problem', 'reflection', 'other')
                ),
                last_practice_ref  TEXT,
                created_at         TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at         TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (target_type, target_id, signal_type)
            )
            """
        )
        changes.append("learner_signals")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidate_status "
        "ON candidate_problems(status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidate_attempts_candidate_id "
        "ON candidate_attempts(candidate_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_learner_signals_target "
        "ON learner_signals(target_type, target_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_learner_signals_weight "
        "ON learner_signals(weight)"
    )
    return changes


def ensure_workbench_schema(conn: sqlite3.Connection) -> List[str]:
    """Apply the workbench review-schedule and feedback-event schema idempotently."""
    changes: List[str] = []

    if not table_exists(conn, "review_schedule"):
        conn.execute(
            """
            CREATE TABLE review_schedule (
                item_type        TEXT NOT NULL CHECK (item_type IN ('kp', 'problem')),
                item_id          TEXT NOT NULL,
                direction        TEXT NOT NULL DEFAULT '',
                state            TEXT NOT NULL DEFAULT 'learning'
                                 CHECK (state IN ('learning', 'review', 'relearning')),
                repetitions      INTEGER NOT NULL DEFAULT 0,
                ease             REAL NOT NULL DEFAULT 2.5,
                interval_days    REAL NOT NULL DEFAULT 0,
                due_at           TEXT,
                last_rating      INTEGER CHECK (last_rating BETWEEN 1 AND 5),
                last_reviewed_at TEXT,
                PRIMARY KEY (item_type, item_id, direction)
            )
            """
        )
        changes.append("review_schedule")

    if not table_exists(conn, "feedback_events"):
        conn.execute(
            """
            CREATE TABLE feedback_events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type  TEXT NOT NULL CHECK (item_type IN ('kp', 'problem')),
                item_id    TEXT NOT NULL,
                rating     INTEGER CHECK (rating BETWEEN 1 AND 5),
                note       TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        changes.append("feedback_events")

    if table_exists(conn, "knowledge_points"):
        changes.extend(
            ensure_columns(
                conn,
                "knowledge_points",
                [("figure_paths", "TEXT")],
            )
        )
    if table_exists(conn, "problems"):
        changes.extend(
            ensure_columns(
                conn,
                "problems",
                [("figure_paths", "TEXT")],
            )
        )
    if table_exists(conn, "problem_attempts"):
        changes.extend(
            ensure_columns(
                conn,
                "problem_attempts",
                [("answer_text", "TEXT")],
            )
        )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_schedule_due "
        "ON review_schedule(due_at)"
    )
    return changes
