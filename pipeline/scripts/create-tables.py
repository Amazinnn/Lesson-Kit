#!/usr/bin/env python3
"""
Pipeline Step 1: Create lesson-kit pool SQLite database.

Creates the active knowledge, problem, candidate, progress, and learner-signal
tables and indexes defined in the lesson-kit pool contract.

Usage:
    python pipeline/scripts/create-tables.py --db pool/dld.db [--force]

Notes:
    - If the DB file doesn't exist, it is created.
    - If tables already exist, the script exits with code 2 unless --force.
    - --force drops all active and retired pool tables and recreates them
      (DESTROYS DATA).
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path


POOL_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "pool" / "scripts"
if str(POOL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(POOL_SCRIPT_DIR))

from pool_schema import ensure_problem_candidate_schema  # noqa: E402
from pool_schema import ensure_workbench_schema  # noqa: E402


SCHEMA_SQL = """
-- knowledge_points: persistent KP asset
CREATE TABLE knowledge_points (
    kp_id           TEXT PRIMARY KEY,
    knowledge_item  TEXT NOT NULL,
    graph_label     TEXT,  -- short audited label for map-like graph nodes
    source_location TEXT,
    knowledge_type  TEXT NOT NULL CHECK (knowledge_type IN (
                        'concept-property', 'method-modeling',
                        'formula-calculation', 'algorithm-process',
                        'code-implementation', 'system-timing',
                        'lab-implementation', 'memory-recall'
                    )),
    related_kp_ids  TEXT,  -- JSON array: ["dld-ch02-kp-003"]
    importance      TEXT NOT NULL CHECK (importance IN (
                        'core', 'supplementary', 'optional'
                    )),
    learning_action TEXT,
    body            TEXT,
    difficulty      INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    fragile         TEXT,  -- NULL = not fragile; non-NULL = Markdown fragility note
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_kp_type       ON knowledge_points(knowledge_type);
CREATE INDEX idx_kp_importance ON knowledge_points(importance);
CREATE INDEX idx_kp_difficulty ON knowledge_points(difficulty);
CREATE INDEX idx_kp_fragile    ON knowledge_points(fragile);

-- knowledge_relations: audited low-level course network edges
CREATE TABLE knowledge_relations (
    relation_id   TEXT PRIMARY KEY,
    source_kp_id  TEXT NOT NULL REFERENCES knowledge_points(kp_id),
    target_kp_id  TEXT NOT NULL REFERENCES knowledge_points(kp_id),
    relation_type TEXT NOT NULL CHECK (relation_type IN (
                      'prerequisite', 'part_of', 'contrasts',
                      'generalizes', 'variant_of', 'applies_to'
                  )),
    direction     TEXT NOT NULL CHECK (direction IN ('directed', 'symmetric')),
    strength      TEXT NOT NULL CHECK (strength IN ('high', 'medium', 'low')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (source_kp_id <> target_kp_id),
    UNIQUE (source_kp_id, target_kp_id, relation_type)
);

CREATE INDEX idx_knowledge_relations_source ON knowledge_relations(source_kp_id);
CREATE INDEX idx_knowledge_relations_target ON knowledge_relations(target_kp_id);
CREATE INDEX idx_knowledge_relations_type   ON knowledge_relations(relation_type);

-- questions: chapter companion MCQs (kept for design intent; not populated by Create)
CREATE TABLE questions (
    q_id               TEXT PRIMARY KEY,
    question_text      TEXT NOT NULL,
    answer_key         TEXT NOT NULL,
    answer_explanation TEXT,
    kp_id              TEXT NOT NULL,
    difficulty         INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    FOREIGN KEY (kp_id) REFERENCES knowledge_points(kp_id)
);

CREATE INDEX idx_q_kp         ON questions(kp_id);
CREATE INDEX idx_q_difficulty ON questions(difficulty);

-- kp_progress: per-KP absorption state (overwritten on change)
CREATE TABLE kp_progress (
    kp_id           TEXT PRIMARY KEY REFERENCES knowledge_points(kp_id),
    mastery_state   TEXT NOT NULL DEFAULT 'new'
                    CHECK (mastery_state IN (
                        'new', 'confused', 'grasping', 'stable', 'faded'
                    )),
    self_assessment TEXT
);

-- question_progress: append-only interaction log
CREATE TABLE question_progress (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    q_id          TEXT NOT NULL REFERENCES questions(q_id),
    note          TEXT NOT NULL,
    mastery_state TEXT NOT NULL DEFAULT 'new'
                  CHECK (mastery_state IN (
                      'new', 'confused', 'misleaded', 'familiar', 'mastered'
                  )),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_qp_q_id ON question_progress(q_id);

-- problems: durable problem pool. Source-specific pools are logical filters
-- over source_kind, not separate physical tables.
CREATE TABLE problems (
    problem_id   TEXT PRIMARY KEY,
    kp_ids       TEXT NOT NULL,  -- JSON array: ["dmath-ch06-kp-001", ...]
    problem_text TEXT NOT NULL,
    solution     TEXT,
    problem_type TEXT NOT NULL CHECK (problem_type IN (
                     'calculation', 'proof', 'modeling',
                     'explanation', 'experiment', 'design',
                     'application', 'counterexample', 'other'
                 )),
    source_kind  TEXT NOT NULL CHECK (source_kind IN (
                     'textbook', 'quiz', 'midterm',
                     'final', 'makeup', 'other'
                 )),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_problem_source_kind ON problems(source_kind);
CREATE INDEX idx_problem_type        ON problems(problem_type);

-- problem_progress: current per-problem learning state
CREATE TABLE problem_progress (
    problem_id TEXT PRIMARY KEY REFERENCES problems(problem_id),
    status     TEXT NOT NULL DEFAULT 'new'
               CHECK (status IN (
                   'new', 'wrong', 'stuck', 'reviewing', 'mastered'
               )),
    note       TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_problem_progress_status ON problem_progress(status);

-- problem_attempts: append-only per-problem interaction log
CREATE TABLE problem_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL REFERENCES problems(problem_id),
    status     TEXT NOT NULL
               CHECK (status IN (
                   'new', 'wrong', 'stuck', 'reviewing', 'mastered'
               )),
    note       TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_problem_attempts_problem_id ON problem_attempts(problem_id);
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create the lesson-kit pool SQLite database schema.",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the SQLite database file (will be created if missing).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop existing tables before recreating. DESTROYS DATA.",
    )
    return parser.parse_args(argv)


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def main(argv=None) -> int:
    args = parse_args(argv)

    db_path = args.db
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir and not os.path.isdir(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    existed_before = os.path.isfile(db_path)
    conn = sqlite3.connect(db_path)
    try:
        existing_tables = [
            "candidate_attempts",
            "candidate_problems",
            "learner_signals",
            "knowledge_relations",
            "knowledge_points",
            "questions",
            "problems",
            "kp_progress",
            "question_progress",
            "problem_progress",
            "problem_attempts",
            # Retired draft tables from the pre-v1 problem-pool design.
            "textbook_exercises",
            "exam_questions",
        ]
        any_existing = any(table_exists(conn, t) for t in existing_tables)

        if any_existing and not args.force:
            print(
                f"ERROR: tables already exist in {db_path}. "
                "Use --force to drop and recreate (DESTROYS DATA).",
                file=sys.stderr,
            )
            return 2

        if any_existing and args.force:
            print(f"--force set. Dropping existing tables in {db_path}...")
            for t in existing_tables:
                conn.execute(f"DROP TABLE IF EXISTS {t}")
            conn.commit()

        conn.executescript(SCHEMA_SQL)
        ensure_problem_candidate_schema(conn)
        ensure_workbench_schema(conn)
        conn.commit()

        verb = "Recreated" if any_existing else "Created"
        prefix = "fresh" if not existed_before else "existing"
        print(f"{verb} schema in {prefix} DB: {db_path}")
        print(
            "  - 11 tables: knowledge_points, knowledge_relations, questions, "
            "problems, kp_progress, question_progress, problem_progress, "
            "problem_attempts, candidate_problems, candidate_attempts, learner_signals"
        )
        print("  - 18 indexes")
        return 0
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
