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

    def test_browser_stuck_attempt_is_retry_safe_and_finishes_once(self):
        from workbench.data import active_practice, attempts

        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001"))

        first = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="",
            request_id="stuck-once", practice_position=0, stuck=True)
        replay = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="",
            request_id="stuck-once", practice_position=0, stuck=True)

        self.assertEqual(first["attempt_id"], replay["attempt_id"])
        self.assertEqual(first["status"], "stuck")
        self.assertEqual(len(self.pool.attempts("dmath-ch06-prob-001")), 1)
        self.assertIsNone(active_practice.current(self.pool))

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

    def test_finished_and_replaced_practices_are_archived(self):
        from workbench.data import active_practice

        self.add_problem("dmath-ch06-prob-002")
        active_practice.create(
            self.pool,
            self.payload("dmath-ch06-prob-001", "dmath-ch06-prob-002"),
        )
        active_practice.mark(self.pool, 0, "stuck")
        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-002"), replace=True)
        active_practice.mark(self.pool, 0, "stuck")

        rows = self.pool.connect().execute(
            "SELECT status, source_label, items_json FROM practice_runs ORDER BY id"
        ).fetchall()
        self.assertEqual([row["status"] for row in rows], ["abandoned", "completed"])
        self.assertEqual(rows[0]["source_label"], "临时练习")
        self.assertIn('"state": "stuck"', rows[0]["items_json"])

    def test_archived_practice_can_be_replayed_without_new_history_fields(self):
        from workbench.data import active_practice

        active_practice.create(self.pool, {
            "source_kind": "quick",
            "kp_ids": ["dmath-ch06-kp-001"],
            "practice_mode": "exam",
            "rating_mode": "immediate",
            "items": [{"item_type": "problem", "item_id": "dmath-ch06-prob-001"}],
        })
        active_practice.mark(self.pool, 0, "stuck")
        run_id = self.pool.connect().execute(
            "SELECT id FROM practice_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()["id"]

        replayed = active_practice.replay(self.pool, run_id)
        self.assertEqual(replayed["source_kind"], "quick")
        self.assertEqual(
            [item["item_id"] for item in replayed["items"]],
            ["dmath-ch06-prob-001"],
        )
        self.assertEqual(replayed["progress"]["remaining"], 1)

        active_practice.clear(self.pool)
        self.pool.connect().execute(
            "UPDATE practice_runs SET items_json=? WHERE id=?",
            ('[{"item_type":"problem","item_id":"missing-problem","direction":""}]', run_id),
        )
        with self.assertRaisesRegex(active_practice.ActivePracticeError, "unknown problem"):
            active_practice.replay(self.pool, run_id)

    def test_routes_expose_the_single_current_practice_resource(self):
        from workbench.server import app

        methods = {
            method for method, pattern, _handler in app.ROUTES
            if pattern == "/api/w/{name}/practice/current"
        }
        self.assertEqual(methods, {"GET", "POST", "PATCH", "DELETE"})
        self.assertIn(
            ("POST", "/api/w/{name}/practice/runs/{run_id}/replay"),
            {(method, pattern) for method, pattern, _handler in app.ROUTES},
        )

    def test_off_round_derives_learning_state_from_the_verdict(self):
        from workbench.data import active_practice, attempts

        self.add_problem("dmath-ch06-prob-002")
        active_practice.create(
            self.pool, {**self.payload("dmath-ch06-prob-001", "dmath-ch06-prob-002"),
                        "rating_mode": "off"})

        wrong = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="B", verdict=0,
            request_id="off-1", practice_position=0)
        self.assertEqual(wrong["derived_state"], "wrong")

        right = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-002", answer_text="A", verdict=1,
            request_id="off-2", practice_position=1)
        self.assertEqual(right["derived_state"], "mastered")

        # Progress and schedule moved; no rated feedback event was synthesized.
        conn = self.pool.connect()
        progress = dict(conn.execute(
            "SELECT problem_id, status FROM problem_progress "
            "WHERE problem_id LIKE 'dmath-ch06-prob-00%'").fetchall())
        self.assertEqual(progress, {
            "dmath-ch06-prob-001": "wrong",
            "dmath-ch06-prob-002": "mastered",
        })
        events = conn.execute(
            "SELECT COUNT(*) FROM feedback_events WHERE rating IS NOT NULL").fetchone()[0]
        self.assertEqual(events, 0)
        due = conn.execute(
            "SELECT due_at FROM review_schedule WHERE item_id='dmath-ch06-prob-001' "
            "AND direction=''").fetchone()[0]
        self.assertIsNotNone(due)

    def test_rated_round_still_defers_learning_state_to_the_rating(self):
        from workbench.data import active_practice, attempts

        active_practice.create(
            self.pool, self.payload("dmath-ch06-prob-001"))

        result = attempts.record_browser_attempt(
            self.pool, "dmath-ch06-prob-001", answer_text="A", verdict=1,
            request_id="rated-1", practice_position=0)

        self.assertNotIn("derived_state", result)
        conn = self.pool.connect()
        moved = conn.execute(
            "SELECT COUNT(*) FROM problem_progress WHERE problem_id='dmath-ch06-prob-001'"
        ).fetchone()[0]
        self.assertEqual(moved, 0)


if __name__ == "__main__":
    unittest.main()
