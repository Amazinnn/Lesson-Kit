import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import load_script


class PaperSourceSchemaTests(unittest.TestCase):
    def test_legacy_execution_tables_are_widened_without_losing_rows(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(
                """
                CREATE TABLE active_practice (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    source_kind TEXT NOT NULL CHECK (
                        source_kind IN ('quick', 'practice_set', 'agent')
                    ),
                    source_ref TEXT,
                    source_label TEXT,
                    kp_ids_json TEXT NOT NULL DEFAULT '[]',
                    practice_mode TEXT NOT NULL,
                    rating_mode TEXT NOT NULL,
                    cursor INTEGER NOT NULL DEFAULT 0 CHECK (cursor >= 0),
                    started_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE practice_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_kind TEXT NOT NULL CHECK (
                        source_kind IN ('quick', 'practice_set', 'agent')
                    ),
                    source_ref TEXT,
                    source_label TEXT,
                    kp_ids_json TEXT NOT NULL DEFAULT '[]',
                    practice_mode TEXT NOT NULL,
                    rating_mode TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('completed', 'abandoned')),
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO active_practice
                    (singleton, source_kind, kp_ids_json, practice_mode, rating_mode)
                    VALUES (1, 'quick', '[]', 'exam', 'immediate');
                INSERT INTO practice_runs
                    (source_kind, kp_ids_json, practice_mode, rating_mode, items_json,
                     status, started_at)
                    VALUES ('practice_set', '[]', 'exam', 'immediate', '[]',
                            'completed', datetime('now'));
                """
            )
            schema = load_script(
                "pool_schema_paper_source_test", Path("pool/scripts/pool_schema.py")
            )
            changes = schema.ensure_workbench_schema(conn)

            self.assertIn("active_practice.source_kind-paper", changes)
            self.assertIn("practice_runs.source_kind-paper", changes)
            self.assertEqual(
                conn.execute("SELECT source_kind FROM active_practice").fetchone()[0],
                "quick",
            )
            self.assertEqual(
                conn.execute("SELECT source_kind FROM practice_runs").fetchone()[0],
                "practice_set",
            )

            conn.execute("UPDATE active_practice SET source_kind='paper'")
            conn.execute("UPDATE practice_runs SET source_kind='paper'")
            self.assertEqual(
                conn.execute("SELECT source_kind FROM active_practice").fetchone()[0],
                "paper",
            )
            self.assertEqual(
                conn.execute("SELECT source_kind FROM practice_runs").fetchone()[0],
                "paper",
            )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
