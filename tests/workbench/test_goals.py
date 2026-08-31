"""Explicit workspace goal persistence tests."""

import concurrent.futures
import unittest

from tests.workbench.fixtures import WorkspaceFixture


class GoalStoreTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()

    def tearDown(self):
        self.fixture.cleanup()

    def test_goal_crud_is_explicit_and_roundtrips(self):
        from workbench.data import goals

        root = self.fixture.ws
        self.assertEqual(goals.list_goals(root), [])
        created = goals.create_goal(root, {
            "title": "完成离散数学复习",
            "kind": "long_term",
            "start_date": "2026-09-01",
            "deadline": "2026-09-10",
            "description": "覆盖本章核心内容",
        })
        self.assertEqual(created["id"], "goal-001")
        self.assertEqual(created["start_date"], "2026-09-01")
        self.assertEqual(goals.list_goals(root)[0]["title"], "完成离散数学复习")
        updated = goals.update_goal(root, "goal-001", {
            "title": "完成 ch06 复习", "start_date": "2026-09-02",
        })
        self.assertEqual(updated["title"], "完成 ch06 复习")
        self.assertEqual(updated["start_date"], "2026-09-02")
        self.assertEqual(goals.delete_goal(root, "goal-001")["deleted"], True)
        self.assertEqual(goals.list_goals(root), [])

    def test_mutation_refuses_to_overwrite_a_corrupt_goal_file(self):
        from workbench.data import goals

        path = self.fixture.ws / ".lessonkit" / "goals.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{broken", encoding="utf-8")

        with self.assertRaises(ValueError):
            goals.create_goal(self.fixture.ws, {"title": "must not overwrite"})

        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_goal_period_rejects_a_start_after_its_deadline(self):
        from workbench.data import goals

        with self.assertRaisesRegex(ValueError, "start_date"):
            goals.create_goal(self.fixture.ws, {
                "title": "倒置区间",
                "start_date": "2026-09-11",
                "deadline": "2026-09-10",
            })

    def test_concurrent_creates_do_not_lose_goals_or_reuse_ids(self):
        from workbench.data import goals

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            created = list(executor.map(
                lambda number: goals.create_goal(
                    self.fixture.ws, {"title": f"goal {number}"}
                ),
                range(12),
            ))

        stored = goals.list_goals(self.fixture.ws)
        self.assertEqual(len(stored), 12)
        self.assertEqual(len({item["id"] for item in created}), 12)


if __name__ == "__main__":
    unittest.main()
