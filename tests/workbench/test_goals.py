"""Explicit workspace goal persistence tests."""

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
            "deadline": "2026-09-10",
            "description": "覆盖本章核心内容",
        })
        self.assertEqual(created["id"], "goal-001")
        self.assertEqual(goals.list_goals(root)[0]["title"], "完成离散数学复习")
        updated = goals.update_goal(root, "goal-001", {"title": "完成 ch06 复习"})
        self.assertEqual(updated["title"], "完成 ch06 复习")
        self.assertEqual(goals.delete_goal(root, "goal-001")["deleted"], True)
        self.assertEqual(goals.list_goals(root), [])


if __name__ == "__main__":
    unittest.main()
