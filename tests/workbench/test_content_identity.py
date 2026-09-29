"""The whole-stem key removes export/render noise without merging real variants."""

import unittest

from workbench.domain.content_identity import problem_identity


class ContentIdentityTests(unittest.TestCase):
    def test_case_whitespace_and_punctuation_are_normalized(self):
        self.assertEqual(
            problem_identity("  WHAT,  is this?\n"),
            problem_identity("what is   this"),
        )

    def test_math_delimiters_tex_commands_and_html_sup_are_rendering_variants(self):
        self.assertEqual(problem_identity(r"$x^{2} \leq y$"),
                         problem_identity(r"\(x<sup>2</sup> ≤ y\)"))

    def test_export_noise_lines_do_not_change_the_identity(self):
        source = "题目：求 x + 1。\n(3分)\n作者：张三\n单位：某大学"
        imported = "题目 求 x+1\n创建提问：abc\n评测结果：答案正确"
        self.assertEqual(problem_identity(source), problem_identity(imported))

    def test_whole_stem_is_compared_without_truncation(self):
        prefix = "A long stem " * 80
        self.assertNotEqual(
            problem_identity(prefix + "find x"),
            problem_identity(prefix + "find y"),
        )

    def test_arithmetic_and_grouping_remain_semantic(self):
        self.assertNotEqual(problem_identity("a + b = c"),
                            problem_identity("a - b = c"))
        self.assertNotEqual(problem_identity("(a + b) * c"),
                            problem_identity("a + (b * c)"))

    def test_similar_but_different_stems_remain_distinct(self):
        self.assertNotEqual(problem_identity("求方程的所有正整数解"),
                            problem_identity("求方程的所有整数解"))


if __name__ == "__main__":
    unittest.main()
