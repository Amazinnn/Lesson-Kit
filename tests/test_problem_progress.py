import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = REPO_ROOT / "pool" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

pool_schema = load_script("pool_schema", Path("pool/scripts/pool_schema.py"))
record_problem = load_script("record_problem", Path("pool/scripts/record-problem.py"))
serve_graph = load_script("serve_graph", Path("pool/scripts/serve-graph.py"))


class ProblemProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "pool.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(
            """
            CREATE TABLE knowledge_points (
                kp_id TEXT PRIMARY KEY,
                knowledge_item TEXT NOT NULL,
                source_location TEXT,
                knowledge_type TEXT,
                related_kp_ids TEXT,
                importance TEXT,
                learning_action TEXT,
                body TEXT,
                difficulty INTEGER,
                fragile TEXT,
                updated_at TEXT
            );
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                kp_ids TEXT NOT NULL,
                problem_text TEXT NOT NULL,
                solution TEXT,
                problem_type TEXT NOT NULL,
                source_kind TEXT NOT NULL
            );
            INSERT INTO knowledge_points
            VALUES (
                'dmath-ch06-kp-001',
                '乘法规则',
                'Section 6.1',
                'concept-property',
                '[]',
                'core',
                '',
                'old body',
                2,
                NULL,
                '2026-01-01 00:00:00'
            );
            INSERT INTO problems
            VALUES (
                'dmath-ch06-prob-001',
                '["dmath-ch06-kp-001"]',
                'Count staged choices.',
                'solution must not leak',
                'calculation',
                'textbook'
            );
            """
        )
        self.conn.commit()
        self.conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def test_migration_adds_graph_label_and_progress_tables_idempotently(self):
        conn = self.connect()
        try:
            first = pool_schema.ensure_learning_state_schema(conn)
            conn.commit()
            second = pool_schema.ensure_learning_state_schema(conn)
            conn.commit()
            columns = pool_schema.column_names(conn, "knowledge_points")
        finally:
            conn.close()

        self.assertIn("knowledge_points.graph_label", first)
        self.assertIn("problem_progress", first)
        self.assertIn("problem_attempts", first)
        self.assertEqual(second, [])
        self.assertIn("graph_label", columns)

    def test_record_problem_updates_current_state_and_appends_attempt(self):
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "wrong",
            "missed product-rule independence",
        )
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "reviewing",
            "",
        )

        conn = self.connect()
        try:
            current = conn.execute(
                "SELECT status, note FROM problem_progress WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchone()
            attempts = conn.execute(
                "SELECT status, note FROM problem_attempts WHERE problem_id = ? ORDER BY id",
                ("dmath-ch06-prob-001",),
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual(current, ("reviewing", None))
        self.assertEqual(
            attempts,
            [
                ("wrong", "missed product-rule independence"),
                ("reviewing", None),
            ],
        )

    def test_formal_wrong_and_stuck_attempts_strengthen_kp_signal(self):
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "wrong",
            "first miss",
        )
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "stuck",
            "still blocked",
        )
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "mastered",
            "later success",
        )

        conn = self.connect()
        try:
            signal = conn.execute(
                """
                SELECT target_type, target_id, signal_type, weight,
                       evidence_count, note, last_practice_kind, last_practice_ref
                FROM learner_signals
                """
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(
            signal,
            (
                "node",
                "dmath-ch06-kp-001",
                "weak_node",
                "high",
                2,
                "still blocked",
                "problem",
                "dmath-ch06-prob-001",
            ),
        )

    def test_server_helpers_update_only_scoped_kp_and_problem_state(self):
        serve_graph.update_kp_text(
            self.db_path,
            "dmath",
            "ch06",
            "dmath-ch06-kp-001",
            "new body",
            "fragile note",
        )
        serve_graph.record_problem_status(
            self.db_path,
            "dmath",
            "ch06",
            "dmath-ch06-prob-001",
            "mastered",
            "clean retry",
        )

        conn = self.connect()
        try:
            kp = conn.execute(
                "SELECT body, fragile FROM knowledge_points WHERE kp_id = ?",
                ("dmath-ch06-kp-001",),
            ).fetchone()
            progress = conn.execute(
                "SELECT status, note FROM problem_progress WHERE problem_id = ?",
                ("dmath-ch06-prob-001",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(kp, ("new body", "fragile note"))
        self.assertEqual(progress, ("mastered", "clean retry"))

    def test_server_helpers_reject_out_of_scope_ids(self):
        with self.assertRaises(ValueError):
            serve_graph.update_kp_text(
                self.db_path,
                "dmath",
                "ch06",
                "dmath-ch07-kp-001",
                "bad",
                "",
            )
        with self.assertRaises(ValueError):
            serve_graph.record_problem_status(
                self.db_path,
                "dmath",
                "ch06",
                "dmath-ch07-prob-001",
                "wrong",
                "",
            )

    def test_server_focus_map_reads_signal_file_without_solution_leakage(self):
        signal_path = self.root / "signal-map.json"
        signal_path.write_text(
            json.dumps(
                {
                    "signals": [
                        {
                            "signal_id": "sig:001",
                            "target_type": "node",
                            "target_id": "dmath-ch06-kp-001",
                            "signal_type": "weak_node",
                            "weight": "high",
                            "note": "needs practice",
                            "source": "test",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        packet = serve_graph.load_focus_map(
            self.db_path,
            "dmath",
            "ch06",
            ["dmath-ch06-kp-001"],
            None,
            1,
            10,
            False,
            signal_path,
        )

        self.assertEqual(packet["meta"]["view"], "focus-map")
        self.assertEqual(packet["nodes"][0]["id"], "dmath-ch06-kp-001")
        self.assertEqual(packet["signals"][0]["signal_id"], "sig:001")
        self.assertNotIn("solution must not leak", json.dumps(packet, ensure_ascii=False))

    def test_server_focus_map_reads_sqlite_signals_without_signal_file(self):
        record_problem.record_problem(
            self.db_path,
            "dmath-ch06-prob-001",
            "wrong",
            "needs product-rule practice",
        )

        packet = serve_graph.load_focus_map(
            self.db_path,
            "dmath",
            "ch06",
            ["dmath-ch06-kp-001"],
            None,
            1,
            10,
            False,
            None,
        )

        self.assertEqual(packet["signals"][0]["target_id"], "dmath-ch06-kp-001")
        self.assertEqual(packet["signals"][0]["source"], "problem:dmath-ch06-prob-001")
        self.assertEqual(packet["nodes"][0]["signals"][0]["weight"], "medium")

    def test_server_focus_map_rejects_out_of_scope_seed(self):
        with self.assertRaisesRegex(ValueError, "seed KP not found"):
            serve_graph.load_focus_map(
                self.db_path,
                "dmath",
                "ch06",
                ["dmath-ch07-kp-001"],
                None,
                1,
                10,
                False,
                None,
            )


if __name__ == "__main__":
    unittest.main()
