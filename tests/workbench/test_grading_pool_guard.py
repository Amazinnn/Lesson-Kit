"""Grading on a pool without the additive part-grading tables degrades loudly.

An old pool (no explicit additive migration yet) must produce a readable JSON
error, never a silent dead connection — the HTTP worker used to drop the
request entirely when sqlite3.OperationalError escaped the handler.
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from tests.workbench.fixtures import REPO_ROOT


class GradingOldPoolGuardTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.data.pool import Pool
        from workbench.server import api

        self.api = api
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "legacy.db"
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE problem_attempts (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        self.pool = Pool(root=self.tmp.name, db_path=str(self.db_path),
                         course="dmath", chapter="ch06")
        self.workspace = {"name": "legacy", "path": self.tmp.name,
                          "db": str(self.db_path),
                          "active_course": "dmath", "active_chapter": "ch06"}

    def tearDown(self):
        self.pool.close()
        self.tmp.cleanup()

    def test_grading_read_reports_missing_tables_as_a_json_error(self):
        with self.assertRaises(self.api.ApiError) as ctx:
            self.api.grading_read(self.pool, self.workspace, {"attempt_id": "1"}, {})
        self.assertEqual(ctx.exception.status, 500)
        self.assertIn("migrate-progress", ctx.exception.message)

    def test_grading_write_reports_missing_tables_as_a_json_error(self):
        with self.assertRaises(self.api.ApiError) as ctx:
            self.api.grading_write(
                self.pool, self.workspace, {}, {"action": "retry", "attempt_id": 1})
        self.assertEqual(ctx.exception.status, 500)


if __name__ == "__main__":
    unittest.main()
