"""Reusable saved papers stay separate from active practice progress."""

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

        self.assertEqual(started["source_kind"], "practice_set")
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


if __name__ == "__main__":
    unittest.main()
