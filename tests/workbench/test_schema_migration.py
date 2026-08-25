"""Schema migration tests for the workbench (TDD, red first)."""

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))


def build_old_schema_db(conn):
    """Create a pre-workbench pool: base tables with old columns only."""
    conn.executescript(
        """
        CREATE TABLE knowledge_points (
            kp_id TEXT PRIMARY KEY,
            knowledge_item TEXT NOT NULL,
            body TEXT,
            knowledge_type TEXT,
            importance TEXT
        );
        CREATE TABLE problems (
            problem_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL,
            solution TEXT,
            problem_type TEXT,
            source_kind TEXT
        );
        CREATE TABLE candidate_problems (
            candidate_id TEXT PRIMARY KEY,
            kp_ids TEXT NOT NULL,
            problem_text TEXT NOT NULL
        );
        CREATE TABLE problem_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE learner_signals (
            signal_id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            weight TEXT NOT NULL DEFAULT 'medium',
            note TEXT
        );
        CREATE TABLE knowledge_relations (
            relation_id TEXT PRIMARY KEY,
            source_kp_id TEXT NOT NULL,
            target_kp_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            strength TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO problems VALUES (?, ?, ?, ?, ?, ?)",
        ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "text", "sol", "calculation", "textbook"),
    )
    conn.execute(
        "INSERT INTO problem_attempts (problem_id, status, note) VALUES (?, ?, ?)",
        ("dmath-ch06-prob-001", "wrong", "note"),
    )
    conn.commit()


class WorkbenchSchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "pool.db"
        self.conn = sqlite3.connect(self.db_path)
        build_old_schema_db(self.conn)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def table_names(self):
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {r[0] for r in rows}

    def columns(self, table):
        return {r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")}

    def test_migration_creates_workbench_tables(self):
        pool_schema.ensure_workbench_schema(self.conn)
        tables = self.table_names()
        self.assertIn("review_schedule", tables)
        self.assertIn("feedback_events", tables)

    def test_migration_adds_columns(self):
        pool_schema.ensure_workbench_schema(self.conn)
        self.assertIn("figure_paths", self.columns("knowledge_points"))
        self.assertIn("fragile", self.columns("knowledge_points"))
        self.assertIn("figure_paths", self.columns("problems"))
        self.assertIn("answer_text", self.columns("problem_attempts"))

    def test_migration_adds_problem_metadata_and_current_state(self):
        pool_schema.ensure_workbench_schema(self.conn)
        self.assertIn("display_title", self.columns("problems"))
        self.assertIn("topic_label", self.columns("problems"))
        self.assertIn("display_summary", self.columns("problems"))
        self.assertIn("display_title", self.columns("candidate_problems"))
        self.assertIn("topic_label", self.columns("candidate_problems"))
        self.assertIn("display_summary", self.columns("candidate_problems"))
        self.assertIn("learning_current_state", self.table_names())

    def test_migration_is_idempotent(self):
        pool_schema.ensure_workbench_schema(self.conn)
        self.conn.execute("INSERT INTO review_schedule VALUES (?,?,?,?,?,?,?,?,?,?)", (
            "problem", "dmath-ch06-prob-001", "", "learning", 0, 2.5, 0.0, None, None, None,
        ))
        self.conn.commit()
        pool_schema.ensure_workbench_schema(self.conn)
        rows = self.conn.execute(
            "SELECT COUNT(*) FROM review_schedule"
        ).fetchone()[0]
        self.assertEqual(rows, 1)

    def test_migration_preserves_existing_data(self):
        pool_schema.ensure_workbench_schema(self.conn)
        problems = self.conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        attempts = self.conn.execute("SELECT COUNT(*) FROM problem_attempts").fetchone()[0]
        self.assertEqual(problems, 1)
        self.assertEqual(attempts, 1)
        row = self.conn.execute(
            "SELECT status FROM problem_attempts WHERE problem_id=?",
            ("dmath-ch06-prob-001",),
        ).fetchone()
        self.assertEqual(row[0], "wrong")

    def test_migration_derives_current_state_without_adding_feedback(self):
        pool_schema.ensure_workbench_schema(self.conn)
        self.conn.execute(
            "INSERT INTO feedback_events (item_type, item_id, rating, note) VALUES (?, ?, ?, ?)",
            ("problem", "dmath-ch06-prob-001", 2, "old rating"),
        )
        self.conn.commit()
        pool_schema.ensure_workbench_schema(self.conn)
        state = self.conn.execute(
            "SELECT state FROM learning_current_state WHERE item_type=? AND item_id=?",
            ("problem", "dmath-ch06-prob-001"),
        ).fetchone()
        self.assertEqual(state[0], "needs_work")
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0], 1
        )


if __name__ == "__main__":
    unittest.main()
