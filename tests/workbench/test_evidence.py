"""Read-only historical evidence for one knowledge point."""

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO

from tests.workbench.fixtures import WorkspaceFixture


class KnowledgePointEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.workspace = registry.get_workspace("dmath")
        self.pool = _pool_for(self.workspace)
        conn = self.pool.connect()
        with conn:
            for index in range(10):
                cursor = conn.execute(
                    "INSERT INTO problem_attempts "
                    "(problem_id, status, note, answer_text, verdict, choices, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        "dmath-ch06-prob-001",
                        "mastered" if index == 9 else "wrong",
                        f"attempt note {index}",
                        f"learner answer {index}",
                        1 if index == 9 else 0,
                        json.dumps([f"choice {index}"], ensure_ascii=False),
                        f"2026-10-{index + 1:02d} 09:00:00",
                    ),
                )
                if index == 9:
                    conn.execute(
                        "INSERT INTO feedback_events "
                        "(item_type, item_id, rating, note, attempt_id, created_at) "
                        "VALUES ('problem', ?, ?, ?, ?, ?)",
                        (
                            "dmath-ch06-prob-001",
                            5,
                            "Solid recovery.",
                            cursor.lastrowid,
                            "2026-10-10 09:01:00",
                        ),
                    )

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_kp_evidence_is_recent_bounded_and_human_readable(self):
        from workbench.data import evidence

        result = evidence.for_kp(self.pool, "dmath-ch06-kp-001", limit=3)

        self.assertEqual(result["knowledge_point"]["knowledge_item"], "Counting")
        self.assertEqual(result["returned"], 3)
        self.assertTrue(result["has_more"])
        rows = result["recent_problem_evidence"]
        self.assertEqual(
            [row["created_at"] for row in rows],
            [
                "2026-10-10 09:00:00",
                "2026-10-09 09:00:00",
                "2026-10-08 09:00:00",
            ],
        )
        newest = rows[0]
        self.assertEqual(newest["problem_text"], "P1")
        self.assertEqual(newest["answer_text"], "learner answer 9")
        self.assertEqual(newest["choices"], ["choice 9"])
        self.assertTrue(newest["verdict"])
        self.assertEqual(newest["status"], "mastered")
        self.assertEqual(newest["rating"], 5)
        self.assertEqual(newest["feedback_note"], "Solid recovery.")

    def test_default_limit_stays_small(self):
        from workbench.data import evidence

        result = evidence.for_kp(self.pool, "dmath-ch06-kp-001")
        self.assertEqual(result["limit"], evidence.DEFAULT_LIMIT)
        self.assertEqual(result["returned"], evidence.DEFAULT_LIMIT)
        self.assertTrue(result["has_more"])

    def test_evidence_read_does_not_write_learning_state(self):
        from workbench.data import evidence

        conn = self.pool.connect()
        before = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "problem_attempts", "feedback_events", "learner_signals",
                "learning_current_state", "review_schedule",
            )
        }
        evidence.for_kp(self.pool, "dmath-ch06-kp-001", limit=4)
        after = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in before
        }
        self.assertEqual(after, before)

    def test_invalid_scope_is_explicit(self):
        from workbench.data import evidence

        with self.assertRaises(KeyError):
            evidence.for_kp(self.pool, "dmath-ch06-kp-999")
        with self.assertRaisesRegex(ValueError, "limit"):
            evidence.for_kp(self.pool, "dmath-ch06-kp-001", limit=0)

    def test_installed_cli_lists_evidence_command(self):
        from workbench.cli import entry

        self.assertIn("evidence", entry.command_names())

    def test_data_query_rejects_missing_database_without_creating_it(self):
        from workbench.data import evidence

        self.pool.close()
        db_path = self.fixture.db_path
        db_path.unlink()

        with self.assertRaisesRegex(FileNotFoundError, "database"):
            evidence.for_kp(self.pool, "dmath-ch06-kp-001")
        self.assertFalse(db_path.exists())

    def test_installed_cli_rejects_missing_database_without_creating_it(self):
        from workbench.cli import entry

        self.pool.close()
        db_path = self.fixture.db_path
        db_path.unlink()
        output = StringIO()

        with redirect_stdout(output):
            status = entry.lesson_kit_main([
                "evidence", "dmath", "kp", "dmath-ch06-kp-001",
            ])

        self.assertEqual(status, 2)
        self.assertIn("database", output.getvalue())
        self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
