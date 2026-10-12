"""Pure practice-page turn-focus rules."""

import unittest

from workbench.domain.practice_focus import resolve


class PracticeFocusTests(unittest.TestCase):
    def test_previous_and_recent_references_keep_their_distinct_targets(self):
        previous = ["problem-1", "problem-2"]

        for message in ("上一题我不会做", "上一题为什么做不出来"):
            with self.subTest(message=message):
                self.assertEqual(
                    resolve(message, "problem-3", previous),
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
            "不是刚才那题",
            "不要解释上一题，只解释当前这题",
            "不要解释前一道题",
            "上一题不用解释了",
            "前几题不用管，只讲这题",
            "前几题不要讲了",
            "上一题和这题有什么区别",
            "上一题和这一题有什么区别",
            "上一题和前几题有什么关系",
        )

        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(resolve(message, "problem-3", ["problem-1"]), expected)

    def test_target_negation_covers_supported_references_and_local_modifiers(self):
        references = (
            "上一题", "上一道题", "上题", "前一题", "前一道题",
            "前面那题", "前面那道题", "刚才那题", "刚才那道题",
            "刚刚那题", "刚刚那道题", "前几题", "前几道题",
            "前面几题", "前面几道题", "刚才几题", "刚才几道题",
            "刚刚几题", "刚刚几道题", "最近几题", "最近几道题",
        )
        templates = (
            "不是{}", "并不是 {}", "不要解释{}", "{}不用解释了", "{}不要讲了",
            "不要再解释{}", "{}不用再讲了", "不要解释一下{}",
            "不要 解释 {}", "{} 不用 解释了", "别 再 讲 一下 {}",
            "我不是问{}", "我不是在问{}", "我并不是在问 {}",
        )
        expected = {
            "type": "problem",
            "problem_ids": ["problem-3"],
            "basis": "page_anchor",
        }

        for reference in references:
            for template in templates:
                message = template.format(reference)
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
