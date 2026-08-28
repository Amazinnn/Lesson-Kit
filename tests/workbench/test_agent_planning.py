"""Agent planning boundary: bounded adjustment and baseline fallback."""

import json
import unittest
from datetime import date

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

    def test_recalculated_plan_is_returned_by_the_next_read(self):
        from workbench.server.api import daily_plan, daily_plan_recalculate
        pool = self.pool_for(self.ws)
        try:
            saved = daily_plan_recalculate(
                pool, self.ws, {}, {"adjustment": {"target_count": 2}}
            )["plan"]
            loaded = daily_plan(pool, self.ws, {}, {})
        finally:
            pool.close()
        self.assertEqual(loaded["queue"], saved["queue"])
        self.assertEqual(loaded["plan_version"], 1)
        self.assertEqual(loaded["plan_date"], date.today().isoformat())

    def test_plan_from_another_day_is_not_reused(self):
        from workbench.server.api import daily_plan
        plan_path = self.workspace / ".lessonkit" / "plan.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps({
            "plan_version": 1, "plan_date": "2000-01-01",
            "queue": [{"id": "stale"}], "goals": [], "totals": {},
        }), encoding="utf-8")
        pool = self.pool_for(self.ws)
        try:
            loaded = daily_plan(pool, self.ws, {}, {})
        finally:
            pool.close()
        self.assertNotEqual(loaded["queue"], [{"id": "stale"}])
        self.assertEqual(loaded["plan_date"], date.today().isoformat())

    def test_goal_change_invalidates_a_saved_plan(self):
        from workbench.server.api import daily_plan, daily_plan_recalculate, goals_create
        pool = self.pool_for(self.ws)
        try:
            daily_plan_recalculate(pool, self.ws, {}, {})
            plan_path = self.workspace / ".lessonkit" / "plan.json"
            self.assertTrue(plan_path.is_file())
            goals_create(pool, self.ws, {}, {"title": "准备期末考试"})
            self.assertFalse(plan_path.exists())
            refreshed = daily_plan(pool, self.ws, {}, {})
        finally:
            pool.close()
        self.assertEqual(refreshed["goals"][0]["title"], "准备期末考试")


if __name__ == "__main__":
    unittest.main()
