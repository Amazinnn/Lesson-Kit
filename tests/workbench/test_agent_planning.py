"""Agent planning boundary: bounded adjustment and baseline fallback."""

import json
import unittest

from tests.workbench.fixtures import WorkspaceFixture


class AgentPlanningTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server.api import _pool_for
        self.pool_for = _pool_for
        self.workspace = self.fixture.ws
        self.ws = {"name": "dmath", "path": str(self.workspace),
                   "db": "pool/dmath.db", "active_course": "dmath",
                   "active_chapter": "ch06"}

    def tearDown(self):
        self.fixture.cleanup()

    def test_recalculate_without_agent_returns_baseline(self):
        from workbench.server.api import daily_plan_recalculate
        pool = self.pool_for(self.ws)
        try:
            result = daily_plan_recalculate(pool, self.ws, {}, {})
        finally:
            pool.close()
        self.assertTrue(result["plan"]["queue"])
        self.assertEqual(result["status"], "已更新今日计划")

    def test_adjustment_is_bounded_and_persisted_as_one_plan(self):
        from workbench.server.api import daily_plan_recalculate
        pool = self.pool_for(self.ws)
        try:
            result = daily_plan_recalculate(
                pool, self.ws, {}, {"adjustment": {"target_count": 99}}
            )
        finally:
            pool.close()
        self.assertLessEqual(result["plan"]["totals"]["target_count"], 20)
        saved = self.workspace / ".lessonkit" / "plan.json"
        self.assertTrue(saved.is_file())
        self.assertEqual(json.loads(saved.read_text(encoding="utf-8"))["queue"], result["plan"]["queue"])

    def test_invalid_agent_adjustment_keeps_baseline(self):
        from workbench.server.api import daily_plan_recalculate
        pool = self.pool_for(self.ws)
        try:
            result = daily_plan_recalculate(
                pool, self.ws, {}, {"adjustment": {"queue": "not-a-list"}}
            )
        finally:
            pool.close()
        self.assertTrue(result["plan"]["queue"])
        self.assertEqual(result["status"], "已更新今日计划")


if __name__ == "__main__":
    unittest.main()
