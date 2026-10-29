"""Reusable saved papers stay separate from active practice progress."""

import json
import sys
import unittest

from tests.workbench.fixtures import REPO_ROOT, WorkspaceFixture


class SavedPracticeSetTests(unittest.TestCase):
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
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-002", '["dmath-ch06-kp-001"]',
             "P2", "S2", "calculation", "textbook"),
        )
        self.pool.connect().execute(
            "INSERT INTO problems "
            "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("dmath-ch06-prob-003", '["dmath-ch06-kp-001"]',
             "P3", "S3", "calculation", "textbook"),
        )
        self.pool.commit()

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def test_saved_paper_has_stable_id_and_order(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "第一章综合卷",
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
            request={"source_kinds": ["textbook"]},
        )

        self.assertEqual(saved["practice_set_id"], "ps-001")
        self.assertEqual(saved["count"], 2)
        self.assertEqual(
            [item["problem_id"] for item in saved["plan"]["items"]],
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
        )
        restored = practice_sets.get_saved(self.pool, "ps-001")
        self.assertEqual(restored["practice_set_id"], "ps-001")
        self.assertEqual(len(practice_sets.list_saved(self.pool)), 1)

    def test_reorder_and_render_reuse_the_existing_practice_set_contract(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        updated = practice_sets.update_saved(
            self.pool, saved["practice_set_id"],
            title="重排后的卷子",
            problem_ids=["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
            confirmation=practice_sets.preview_update(
                self.pool, saved['practice_set_id'], title='重排后的卷子',
                problem_ids=['dmath-ch06-prob-002', 'dmath-ch06-prob-001'])['confirmation'],
        )
        rendered = practice_sets.render_saved(self.pool, saved["practice_set_id"])

        self.assertEqual(updated["title"], "重排后的卷子")
        self.assertLess(
            rendered["practice_set"].index("P2"),
            rendered["practice_set"].index("P1"),
        )
        self.assertIn("S2", rendered["solutions"])
        self.assertNotIn("S2", rendered["practice_set"])

    def test_starting_a_saved_paper_copies_items_into_active_practice(self):
        from workbench.data import active_practice, practice_sets
        from workbench.server import api

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-002", "dmath-ch06-prob-001"])

        started = api.practice_set_start(
            self.pool, {}, {"practice_set_id": saved["practice_set_id"]},
            {"practice_mode": "exam", "rating_mode": "immediate"})

        self.assertEqual(started["source_kind"], "paper")
        self.assertEqual(started["source_ref"], "ps-001")
        self.assertEqual(started["source_label"], "卷子")
        self.assertEqual(
            [item["item_id"] for item in started["items"]],
            ["dmath-ch06-prob-002", "dmath-ch06-prob-001"],
        )
        active_practice.mark(self.pool, 0, "stuck")
        active_practice.mark(self.pool, 1, "stuck")
        archived = self.pool.connect().execute(
            "SELECT source_ref, source_label, status FROM practice_runs"
        ).fetchone()
        self.assertEqual(
            tuple(archived), ("ps-001", "卷子", "completed"))
        self.assertIsNone(active_practice.current(self.pool))

    def test_deleting_a_paper_does_not_delete_attempt_history(self):
        from workbench.data import attempts, practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001"])
        attempts.record_result(self.pool, "dmath-ch06-prob-001", "stuck")

        deleted = practice_sets.delete_saved(self.pool, saved["practice_set_id"])

        self.assertTrue(deleted["deleted"])
        self.assertEqual(len(self.pool.attempts("dmath-ch06-prob-001")), 1)
        self.assertEqual(practice_sets.list_saved(self.pool), [])

    def test_appending_a_problem_preserves_active_progress(self):
        from workbench.data import active_practice, practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        paper_id = saved["practice_set_id"]
        active = active_practice.start_saved(
            self.pool, paper_id, reveal_timing="on_submit", rating_mode="off")
        active_practice.mark(self.pool, 0, "stuck")
        before = practice_sets.get_saved(self.pool, paper_id)

        result = practice_sets.append_saved(
            self.pool, paper_id, "dmath-ch06-prob-003")
        after = practice_sets.get_saved(self.pool, paper_id)

        self.assertTrue(result["appended"])
        self.assertEqual(result["position"], 2)
        self.assertEqual(result["mode"], "active")
        self.assertEqual(result["count"], 3)
        self.assertEqual(
            [item["problem_id"] for item in after["plan"]["items"]],
            ["dmath-ch06-prob-001", "dmath-ch06-prob-002",
             "dmath-ch06-prob-003"])
        self.assertEqual(after["progress"], {"total": 3, "completed": 1})
        self.assertEqual(after["generation"], before["generation"] + 1)
        items = [dict(row) for row in self.pool.connect().execute(
            "SELECT position,item_id,state FROM active_practice_items "
            "ORDER BY position")]
        self.assertEqual([item["state"] for item in items],
                         ["stuck", "pending", "pending"])
        self.assertEqual(active_practice.current(self.pool)["execution_id"],
                         active["execution_id"])

    def test_appending_to_a_parked_paper_leaves_the_selected_paper_alone(self):
        from workbench.data import active_practice, practice_sets

        a = practice_sets.create_saved(
            self.pool, "A", ["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        b = practice_sets.create_saved(
            self.pool, "B", ["dmath-ch06-prob-001", "dmath-ch06-prob-002"])
        active_practice.start_saved(
            self.pool, a["practice_set_id"], reveal_timing="on_submit",
            rating_mode="off")
        active_practice.mark(self.pool, 0, "stuck")
        selected = active_practice.start_saved(
            self.pool, b["practice_set_id"], reveal_timing="on_submit",
            rating_mode="off")
        before = [tuple(row) for row in self.pool.connect().execute(
            "SELECT position,item_id,state,attempt_id "
            "FROM active_practice_items ORDER BY position")]

        result = practice_sets.append_saved(
            self.pool, a["practice_set_id"], "dmath-ch06-prob-003")

        after = [tuple(row) for row in self.pool.connect().execute(
            "SELECT position,item_id,state,attempt_id "
            "FROM active_practice_items ORDER BY position")]
        self.assertEqual(result["mode"], "parked")
        self.assertEqual(after, before)
        self.assertEqual(active_practice.current(self.pool)["execution_id"],
                         selected["execution_id"])
        checkpoint = json.loads(self.pool.connect().execute(
            "SELECT checkpoint_json FROM paper_state WHERE paper_id=?",
            (a["practice_set_id"],)).fetchone()[0])
        self.assertEqual(
            [item["item_id"] for item in checkpoint["items"]],
            ["dmath-ch06-prob-001", "dmath-ch06-prob-002",
             "dmath-ch06-prob-003"])
        self.assertEqual(checkpoint["items"][0]["state"], "stuck")
        self.assertEqual(checkpoint["items"][2]["state"], "pending")

    def test_appending_the_same_problem_twice_is_idempotent(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001"])
        paper_id = saved["practice_set_id"]

        first = practice_sets.append_saved(
            self.pool, paper_id, "dmath-ch06-prob-002")
        second = practice_sets.append_saved(
            self.pool, paper_id, "dmath-ch06-prob-002")

        self.assertTrue(first["appended"])
        self.assertFalse(second["appended"])
        self.assertTrue(second["already_present"])
        self.assertEqual(second["position"], 1)
        self.assertEqual(second["count"], 2)
        self.assertEqual(
            len(practice_sets.get_saved(self.pool, paper_id)["plan"]["items"]),
            2)

    def test_appending_an_unknown_problem_writes_nothing(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001"])
        paper_id = saved["practice_set_id"]
        before = practice_sets.get_saved(self.pool, paper_id)

        with self.assertRaises(ValueError):
            practice_sets.append_saved(self.pool, paper_id, "missing-problem")

        after = practice_sets.get_saved(self.pool, paper_id)
        self.assertEqual(after["count"], before["count"])
        self.assertEqual(after["generation"], before["generation"])

    def test_appending_without_progress_changes_only_the_container(self):
        from workbench.data import practice_sets

        saved = practice_sets.create_saved(
            self.pool, "卷子", ["dmath-ch06-prob-001"])
        paper_id = saved["practice_set_id"]

        result = practice_sets.append_saved(
            self.pool, paper_id, "dmath-ch06-prob-002")
        after = practice_sets.get_saved(self.pool, paper_id)

        self.assertEqual(result["mode"], "container")
        self.assertEqual(after["count"], 2)
        self.assertIsNone(after["progress"])
        self.assertEqual(self.pool.connect().execute(
            "SELECT COUNT(*) FROM active_practice").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
