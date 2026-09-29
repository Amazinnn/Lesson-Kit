"""One durable, serial active practice per workspace."""

import os
import sys
import unittest
from pathlib import Path

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class ActivePracticeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        sys.path.insert(0, str(REPO_ROOT / "workbench"))
        from workbench.server import api
        self.pool = api._pool_for({
            "path": str(self.fixture.ws),
            "db": "pool/dmath.db",
            "active_course": "dmath",
            "active_chapter": "ch06",
        })

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def payload(self, *problem_ids):
        return {
            "source_kind": "quick",
            "kp_ids": ["dmath-ch06-kp-001"],
            "practice_mode": "exam",
            "rating_mode": "immediate",
            "items": [
                {"item_type": "problem", "item_id": problem_id}
                for problem_id in problem_ids
            ],
        }

    def add_problem(self, problem_id):
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (problem_id, '["dmath-ch06-kp-001"]', problem_id, "S",
             "calculation", "textbook"),
        )
        self.pool.commit()

    def test_only_one_active_practice_exists_until_explicit_replace(self):
        from workbench.data import active_practice

        self.add_problem("dmath-ch06-prob-002")
        first = active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001", "dmath-ch06-prob-002"))
        self.assertEqual(first["progress"]["total"], 2)
        self.assertEqual(first["cursor"], 0)

        with self.assertRaises(active_practice.ActivePracticeConflict):
            active_practice.create(
                self.pool, self.payload("dmath-ch06-prob-002"))

        replaced = active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-002"), replace=True)
        self.assertEqual(
            [item["item_id"] for item in replaced["items"]],
            ["dmath-ch06-prob-002"],
        )
        self.assertEqual(replaced["progress"]["completed"], 0)

    def test_answer_attempt_and_progress_advance_in_one_write_path(self):
        from workbench.data import active_practice, attempts

        self.add_problem("dmath-ch06-prob-002")
        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001", "dmath-ch06-prob-002"))

        result = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="answer",
            request_id="answer-1", practice_position=0)

        self.assertTrue(result["recorded"])
        self.assertFalse(result["practice"]["completed"])
        current = active_practice.current(self.pool)
        self.assertEqual(current["cursor"], 1)
        self.assertEqual(current["progress"], {
            "completed": 1, "answered": 1, "stuck": 0,
            "remaining": 1, "total": 2,
        })
        self.assertEqual(current["items"][0]["attempt_id"], result["attempt_id"])

    def test_stuck_is_learning_evidence_and_finishing_clears_only_execution_state(self):
        from workbench.data import active_practice, attempts

        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001"))

        result = attempts.record_result(
            self.pool, "dmath-ch06-prob-001", "stuck",
            practice_position=0)

        self.assertTrue(result["practice"]["completed"])
        self.assertIsNone(active_practice.current(self.pool))
        rows = self.pool.attempts("dmath-ch06-prob-001")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "stuck")
        self.assertEqual(rows[0]["id"], result["attempt_id"])

    def test_replacing_execution_state_never_deletes_attempt_history(self):
        from workbench.data import active_practice, attempts

        self.add_problem("dmath-ch06-prob-002")
        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001", "dmath-ch06-prob-002"))
        attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="kept",
            request_id="answer-keep", practice_position=0)

        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-002"), replace=True)

        attempts_kept = self.pool.attempts("dmath-ch06-prob-001")
        self.assertEqual(len(attempts_kept), 1)
        self.assertEqual(attempts_kept[0]["answer_text"], "kept")

    def test_routes_expose_the_single_current_practice_resource(self):
        from workbench.server import app

        methods = {
            method for method, pattern, _handler in app.ROUTES
            if pattern == "/api/w/{name}/practice/current"
        }
        self.assertEqual(methods, {"GET", "POST", "PATCH", "DELETE"})


if __name__ == "__main__":
    unittest.main()
