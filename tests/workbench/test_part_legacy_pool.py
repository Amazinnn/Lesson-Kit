"""Pools without the additive part-grading schema keep the legacy path working.

Reading a practice run, submitting a subjective answer and explicit grading all
run against pools that have not received the explicit migration. Reads and
submissions must degrade to the pre-migration behaviour; explicit grading must
fail with an actionable message instead of a raw sqlite error.
"""

import sqlite3
import unittest
from pathlib import Path

from tests.workbench.fixtures import WorkspaceFixture


class LegacyPoolPartFallbackTests(unittest.TestCase):
    def setUp(self):
        import sys
        from tests.workbench.fixtures import REPO_ROOT

        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.data import part_grading, part_practice, paper_progress, practice_sets
        from workbench.bridge import grading
        from workbench.data.pool import Pool

        self.part_grading = part_grading
        self.part_practice = part_practice
        self.grading = grading
        self.fixture = WorkspaceFixture()
        self.legacy_db = self._legacy_copy()
        self.pool = Pool(root=self.fixture.ws, db_path=str(self.legacy_db),
                         course="dmath", chapter="ch06")
        conn = self.pool.connect()
        conn.execute(
            "INSERT OR IGNORE INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind,"
            " source_answer) VALUES (?,?,?,?,?,?,?)",
            ("dmath-ch06-prob-001", '["dmath-ch06-kp-001"]', "求值", "解", "calculation",
             "textbook", "42"),
        )
        conn.commit()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def _legacy_copy(self):
        """Copy the fixture pool and strip exactly what the migration adds."""
        import shutil

        legacy = Path(self.fixture.ws) / "pool" / "legacy.db"
        shutil.copy(self.fixture.db_path, legacy)
        conn = sqlite3.connect(legacy)
        for table in ("part_attempt_context", "part_grading_revisions", "part_grading_jobs"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        for column in ("part_id", "content_revision"):
            conn.execute(f"ALTER TABLE problem_attempts DROP COLUMN {column}")
        conn.execute("ALTER TABLE problems DROP COLUMN parts")
        conn.commit()
        conn.close()
        return legacy

    def _item(self):
        return {
            "item_type": "problem", "item_id": "dmath-ch06-prob-001",
            "position": 0, "content_revision": 1, "attempt_id": 1,
            "attempt": {"answer_text": "我的作答"},
            "payload": {"problem_type": "calculation", "source_answer": "42",
                        "solution": "解"},
            "draft": {"answer": "我的作答"},
        }

    def test_project_degrades_instead_of_reading_missing_tables(self):
        practice = {"reveal_timing": None, "items": [self._item()]}
        projected = self.part_practice.project(self.pool, practice)
        item = projected["items"][0]
        self.assertEqual(item["part_summary"]["grading"], {"not_requested": 1})
        child = item["part_items"][0]
        self.assertEqual(child["grading_status"], "not_requested")
        self.assertIsNone(child["grading"])

    def test_submit_records_the_legacy_attempt_without_part_storage(self):
        practice = {"execution_id": 7}
        ids = self.part_practice._submit_item(
            self.pool, practice, self._item(),
            [{"id": "whole", "prompt": "", "type": "open_response",
              "short_answer": False}])
        self.assertEqual(len(ids), 1)
        row = self.pool.connect().execute(
            "SELECT answer_text FROM problem_attempts WHERE id=?", (ids[0],)).fetchone()
        self.assertEqual(row["answer_text"], "我的作答")
        tables = {r[0] for r in self.pool.connect().execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("part_grading_jobs", tables)

    def test_explicit_grading_fails_with_the_migration_command(self):
        for call in (
            lambda: self.grading.retry(self.pool, 1),
            lambda: self.grading.apply(self.pool, {
                "attempt_id": 1, "problem_id": "dmath-ch06-prob-001", "part_id": "whole",
                "content_revision": 1, "expected_revision": 0, "operation_id": "op-1",
                "payload": {"process_conclusion": "correct"},
            }),
        ):
            with self.assertRaisesRegex(ValueError, "migrate-progress"):
                call()

    def test_schema_gap_reports_every_missing_piece(self):
        conn = self.pool.connect()
        missing = self.part_grading.missing_schema(conn)
        self.assertIn("part_grading_revisions", missing)
        self.assertIn("problems.parts", missing)
        ready = sqlite3.connect(self.fixture.db_path)
        try:
            self.assertEqual(self.part_grading.missing_schema(ready), [])
        finally:
            ready.close()

    def test_doctor_flags_a_legacy_pool_with_the_migration_command(self):
        from unittest import mock

        from workbench.cli import doctor

        workspace = {"name": "legacy", "path": str(self.fixture.ws),
                     "db": "pool/legacy.db"}
        with mock.patch.object(doctor.registry, "list_workspaces",
                               return_value=[workspace]):
            checks, _ = doctor._check_workspaces()
        flagged = [entry for entry in checks if entry[0].endswith("part grading schema")]
        self.assertEqual(len(flagged), 1)
        self.assertFalse(flagged[0][1])
        self.assertIn("migrate-progress", flagged[0][2])


if __name__ == "__main__":
    unittest.main()
