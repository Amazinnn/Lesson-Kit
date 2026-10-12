"""Pure practice-page turn-focus rules."""

import unittest

from workbench.domain.practice_focus import resolve


class PracticeFocusTests(unittest.TestCase):
    def test_previous_and_recent_references_keep_their_distinct_targets(self):
        previous = ["problem-1", "problem-2"]

        self.assertEqual(
            resolve("上一题我不会做", "problem-3", previous),
            {
                "type": "problem",
                "problem_ids": ["problem-2"],
                "basis": "user_previous_reference",
            },
        )
        self.assertEqual(
            resolve("前几题我都没理解", "problem-3", previous),
            {
                "type": "problem",
                "problem_ids": previous,
                "basis": "user_recent_reference",
            },
        )

    def test_negated_competing_and_multiple_relative_references_keep_page_default(self):
        expected = {
            "type": "problem",
            "problem_ids": ["problem-3"],
            "basis": "page_anchor",
        }
        messages = (
            "不是上一题，是这题",
            "不要解释上一题，只解释当前这题",
            "前几题不用管，只讲这题",
            "上一题和这题有什么区别",
            "上一题和前几题有什么关系",
        )

        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(resolve(message, "problem-3", ["problem-1"]), expected)

    def test_page_default_needs_a_managed_visible_problem(self):
        self.assertIsNone(resolve("上一题", None, ["problem-1"]))
        self.assertEqual(
            resolve("这题", "problem-3", []),
            {
                "type": "problem",
                "problem_ids": ["problem-3"],
                "basis": "page_anchor",
            },
        )


if __name__ == "__main__":
    unittest.main()
