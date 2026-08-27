"""Deterministic daily planning rules."""

from datetime import datetime, timedelta
import unittest

from workbench.domain.planning import build_baseline_plan


class PlanningTests(unittest.TestCase):
    def facts(self):
        now = datetime(2026, 8, 28, 9, 0)
        return {
            "course": "dmath",
            "chapter": "ch06",
            "goals": [
                {"id": "course", "kind": "long_term", "title": "完成离散数学"},
                {"id": "exam", "kind": "stage", "title": "准备章节测验",
                 "deadline": (now + timedelta(days=2)).isoformat()},
            ],
            "kps": [
                {"kp_id": "kp-002", "knowledge_item": "排列组合", "importance": "supplementary"},
                {"kp_id": "kp-001", "knowledge_item": "计数原理", "importance": "core"},
            ],
            "problems": [
                {"problem_id": "p-1", "kp_ids": ["kp-001"], "problem_type": "calculation", "difficulty": 4},
                {"problem_id": "p-2", "kp_ids": ["kp-001"], "problem_type": "choice", "difficulty": 2},
                {"problem_id": "p-3", "kp_ids": ["kp-002"], "problem_type": "choice", "difficulty": 1},
            ],
            "progress": {"kp-001": {"completed": 1, "total": 4}, "kp-002": {"completed": 0, "total": 1}},
            "signals": [{"target_id": "kp-002", "weight": "high"}],
            "schedule": [{"item_type": "kp", "item_id": "kp-001", "due_at": "2026-08-28"}],
        }

    def test_course_order_is_stable_and_repeatable(self):
        facts = self.facts()
        first = build_baseline_plan(facts, now=datetime(2026, 8, 28, 9, 0))
        second = build_baseline_plan(facts, now=datetime(2026, 8, 28, 9, 0))
        self.assertEqual(first, second)
        self.assertEqual([item["kp_ids"] for item in first["queue"]], [["kp-002"], ["kp-001"]])

    def test_deadline_and_coverage_raise_target(self):
        plan = build_baseline_plan(self.facts(), now=datetime(2026, 8, 28, 9, 0))
        item = next(item for item in plan["queue"] if item["kp_ids"] == ["kp-001"])
        self.assertGreaterEqual(item["target_count"], 2)
        self.assertIn("覆盖", item["reason"])

    def test_problem_types_and_missing_values_have_defaults(self):
        facts = self.facts()
        facts["problems"].append({"problem_id": "p-4", "kp_ids": ["kp-002"]})
        plan = build_baseline_plan(facts, now=datetime(2026, 8, 28, 9, 0), available_minutes=30)
        self.assertIn("choice", plan["queue"][1]["difficulty_mix"])
        self.assertGreater(plan["queue"][1]["target_count"], 0)
        self.assertEqual(plan["totals"]["available_minutes"], 30)


if __name__ == "__main__":
    unittest.main()
