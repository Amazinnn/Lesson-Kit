#!/usr/bin/env python3
"""Record durable problem-solving progress in a lesson-kit pool."""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pool_schema import PROBLEM_STATES, ensure_learning_state_schema, table_exists  # noqa: E402


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record a status update for a durable lesson-kit problem.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    parser.add_argument("--problem", required=True, help="Problem ID to record.")
    parser.add_argument(
        "--status",
        required=True,
        choices=PROBLEM_STATES,
        help="Problem status: new, wrong, stuck, reviewing, mastered.",
    )
    parser.add_argument(
        "--note",
        default="",
        help="Optional note, wrong reason, or next review action.",
    )
    return parser.parse_args(argv)


def problem_exists(conn: sqlite3.Connection, problem_id: str) -> bool:
    if not table_exists(conn, "problems"):
        return False
    row = conn.execute(
        "SELECT 1 FROM problems WHERE problem_id = ?",
        (problem_id,),
    ).fetchone()
    return row is not None


def record_problem(
    db_path: Path,
    problem_id: str,
    status: str,
    note: str = "",
) -> None:
    if status not in PROBLEM_STATES:
        raise ValueError(f"invalid status: {status}")
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        if not problem_exists(conn, problem_id):
            raise ValueError(f"problem not found: {problem_id}")
        ensure_learning_state_schema(conn)
        clean_note = note.strip() or None
        conn.execute(
            """
            INSERT INTO problem_progress (problem_id, status, note, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(problem_id) DO UPDATE SET
                status = excluded.status,
                note = excluded.note,
                updated_at = datetime('now')
            """,
            (problem_id, status, clean_note),
        )
        conn.execute(
            """
            INSERT INTO problem_attempts (problem_id, status, note)
            VALUES (?, ?, ?)
            """,
            (problem_id, status, clean_note),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        record_problem(Path(args.db), args.problem, args.status, args.note)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    note_suffix = " with note" if args.note.strip() else ""
    print(f"Recorded {args.problem}: {args.status}{note_suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
