#!/usr/bin/env python3
"""Migrate an existing lesson-kit pool for graph labels and problem progress."""

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pool_schema import ensure_learning_state_schema  # noqa: E402


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add graph_label and problem progress tables to an existing lesson-kit pool.",
    )
    parser.add_argument("--db", required=True, help="Path to SQLite DB.")
    return parser.parse_args(argv)


def migrate_db(db_path: Path) -> list[str]:
    if not db_path.is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        changes = ensure_learning_state_schema(conn)
        conn.commit()
        return changes
    finally:
        conn.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        changes = migrate_db(Path(args.db))
    except (OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if changes:
        print(f"Migrated {os.fspath(args.db)}:")
        for change in changes:
            print(f"  - {change}")
    else:
        print(f"No migration needed: {os.fspath(args.db)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
