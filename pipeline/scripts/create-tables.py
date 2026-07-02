#!/usr/bin/env python3
"""
Pipeline Step 1: Create lesson-kit pool SQLite database.

Creates the 4 tables (knowledge_points, questions, kp_progress,
question_progress) and 6 indexes defined in kp-pool-modular-views.md.

Usage:
    python pipeline/scripts/create-tables.py --db pool/dld-ch02.db [--force]

Notes:
    - If the DB file doesn't exist, it is created.
    - If tables already exist, the script exits with code 2 unless --force.
    - --force drops all 4 tables and recreates them (DESTROYS DATA).
"""

import argparse
import os
import sqlite3
import sys


SCHEMA_SQL = """
-- knowledge_points: persistent KP asset
CREATE TABLE knowledge_points (
    kp_id           TEXT PRIMARY KEY,
    knowledge_item  TEXT NOT NULL,
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
    difficulty      INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    fragile         INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_kp_type       ON knowledge_points(knowledge_type);
CREATE INDEX idx_kp_importance ON knowledge_points(importance);
CREATE INDEX idx_kp_difficulty ON knowledge_points(difficulty);
CREATE INDEX idx_kp_fragile    ON knowledge_points(fragile);

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
            "knowledge_points",
            "questions",
            "kp_progress",
            "question_progress",
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
        conn.commit()

        verb = "Recreated" if any_existing else "Created"
        prefix = "fresh" if not existed_before else "existing"
        print(f"{verb} schema in {prefix} DB: {db_path}")
        print(f"  - 4 tables: knowledge_points, questions, kp_progress, question_progress")
        print(f"  - 6 indexes: idx_kp_type/importance/difficulty/fragile, idx_q_kp/difficulty, idx_qp_q_id")
        return 0
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())