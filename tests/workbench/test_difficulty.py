"""Objective problem difficulty rules and transactions."""

from decimal import Decimal
import unittest

from tests.workbench.fixtures import WorkspaceFixture


class DifficultyRuleTests(unittest.TestCase):
    def test_equal_mean_rounds_quarters_half_up(self):
        from workbench.domain import difficulty

        self.assertEqual(
            difficulty.score({
                "knowledge_breadth": 2,
                "reasoning_depth": 2,
                "transfer_distance": 2,
                "construction_openness": 3,
            }),
            Decimal("2.3"),
        )
        self.assertEqual(
            difficulty.score({
                "knowledge_breadth": 2,
                "reasoning_depth": 2,
                "transfer_distance": 3,
                "construction_openness": 4,
            }),
            Decimal("2.8"),
        )
        self.assertEqual(difficulty.MODEL_ID, "cognitive-v1-equal-mean")

    def test_vector_requires_all_four_integer_dimensions(self):
        from workbench.domain import difficulty

        with self.assertRaisesRegex(ValueError, "missing dimension"):
            difficulty.score({"knowledge_breadth": 2})
        with self.assertRaisesRegex(ValueError, "integer from 1 to 5"):
            difficulty.score({
                "knowledge_breadth": 2,
                "reasoning_depth": True,
                "transfer_distance": 3,
                "construction_openness": 4,
            })


class DifficultyTransactionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench import registry
        from workbench.server.api import _pool_for

        self.pool = _pool_for(registry.get_workspace("dmath"))
        self.problem_id = "dmath-ch06-prob-001"

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def manifest(self, breadth=2):
        return {"items": [{
            "problem_id": self.problem_id,
            "knowledge_breadth": breadth,
            "reasoning_depth": 2,
            "transfer_distance": 2,
            "construction_openness": 3,
        }]}

    def test_check_previews_without_writing_and_apply_writes_complete_vector(self):
        from workbench.data import difficulty as difficulty_data

        preview = difficulty_data.check(self.pool, self.manifest())
        self.assertEqual(preview["items"][0]["difficulty"], 2.3)
        self.assertIsNone(self.pool.problem(self.problem_id)["difficulty"])

        applied = difficulty_data.apply(self.pool, self.manifest())
        row = self.pool.problem(self.problem_id)
        self.assertEqual(applied["updated"], 1)
        self.assertEqual(row["difficulty"], 2.3)
        self.assertEqual(row["difficulty_knowledge_breadth"], 2)
        self.assertEqual(row["difficulty_model"], "cognitive-v1-equal-mean")

    def test_apply_is_atomic_and_overwrites_existing_rating(self):
        from workbench.data import difficulty as difficulty_data

        difficulty_data.apply(self.pool, self.manifest())
        difficulty_data.apply(self.pool, self.manifest(breadth=4))
        self.assertEqual(self.pool.problem(self.problem_id)["difficulty"], 2.8)

        bad = self.manifest(breadth=5)
        bad["items"].append({
            "problem_id": "missing",
            "knowledge_breadth": 1,
            "reasoning_depth": 1,
            "transfer_distance": 1,
            "construction_openness": 1,
        })
        with self.assertRaisesRegex(ValueError, "unknown problem"):
            difficulty_data.apply(self.pool, bad)
        self.assertEqual(self.pool.problem(self.problem_id)["difficulty"], 2.8)

    def test_cognitive_content_update_clears_the_complete_rating(self):
        from workbench.data import content
        from workbench.data import difficulty as difficulty_data

        difficulty_data.apply(self.pool, self.manifest())
        content.update(self.pool, "problem", self.problem_id, {"problem_text": "Changed"})
        row = self.pool.problem(self.problem_id)
        self.assertIsNone(row["difficulty"])
        self.assertIsNone(row["difficulty_model"])
        self.assertIsNone(row["difficulty_knowledge_breadth"])


if __name__ == "__main__":
    unittest.main()
