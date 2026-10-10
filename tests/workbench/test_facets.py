"""Filter facets: the document-key rule and the per-pool dimension census."""

import unittest

from workbench.domain import facets


class DocumentKeyTests(unittest.TestCase):
    def test_an_md_evidence_carries_the_document(self):
        self.assertEqual(
            facets.document_key("题库/midterm·CC98_topic6342400_合集.md 第1题"),
            "题库/midterm·CC98_topic6342400_合集.md",
        )

    def test_a_line_anchor_suffix_does_not_confuse_the_key(self):
        self.assertEqual(
            facets.document_key("题库/期末/真题.md#L29｜题号 fin-p01-s1-q2"),
            "题库/期末/真题.md",
        )

    def test_textbook_rows_fold_into_one_key(self):
        self.assertEqual(facets.document_key("教材 第12章 习题12-1"), "教材")

    def test_an_unknown_format_degrades_to_its_first_segment(self):
        self.assertEqual(facets.document_key("某来源 · 某卷"), "某来源 · 某卷")
        self.assertEqual(facets.document_key(None), "")
        self.assertEqual(facets.document_key("  "), "")


class PoolFacetsTests(unittest.TestCase):
    def test_counts_come_from_actual_rows_and_sort_by_count(self):
        class FakePool:
            def problems_all(self):
                return [
                    {"source_kind": "midterm", "exam_year": "2024-2025秋冬",
                     "source_evidence": "题库/midterm·A.md 第1题",
                     "origin_kind": "source_problem"},
                    {"source_kind": "midterm", "exam_year": "2024-2025秋冬",
                     "source_evidence": "题库/midterm·A.md 第2题",
                     "origin_kind": "source_problem"},
                    {"source_kind": "final", "exam_year": None,
                     "source_evidence": "教材 第3章", "origin_kind": "adapted_problem"},
                    {"source_kind": None, "exam_year": None, "source_evidence": None,
                     "origin_kind": None},
                ]

        facets_result = facets.pool_facets(FakePool())

        self.assertEqual(facets_result["source_kinds"],
                         [{"value": "midterm", "count": 2},
                          {"value": "final", "count": 1}])
        self.assertEqual(facets_result["exam_years"],
                         [{"value": "2024-2025秋冬", "count": 2}])
        self.assertEqual(facets_result["docs"],
                         [{"value": "题库/midterm·A.md", "count": 2},
                          {"value": "教材", "count": 1}])
        self.assertEqual(facets_result["origin_kinds"],
                         [{"value": "source_problem", "count": 2},
                          {"value": "adapted_problem", "count": 1}])


class KeywordDomainTests(unittest.TestCase):
    PROBLEM = {
        "display_title": "计数原理",
        "problem_text": "【2023期末】【合集A】计算 1+2+3",
        "source_evidence": "题库/final·A.md 第2题",
        "exam_year": "2023-2024秋冬",
    }

    def test_keywords_split_on_whitespace_and_casefold(self):
        self.assertEqual(facets.keyword_words(" Counting  原理 "), ["counting", "原理"])
        self.assertEqual(facets.keyword_words(["A b", "C"]), ["a", "b", "c"])
        self.assertEqual(facets.keyword_words(None), [])

    def test_the_stem_domain_is_what_the_problem_says(self):
        stem = facets.stem_text(self.PROBLEM)
        for word in ("计数原理", "1+2+3"):
            self.assertTrue(facets.matches_all(stem, [word.casefold()]), word)
        for word in ("final·A", "2023-2024"):
            self.assertFalse(facets.matches_all(stem, [word.casefold()]), word)

    def test_the_stem_domain_ignores_retired_problem_fields(self):
        legacy_problem = {**self.PROBLEM, "topic_label": "算术"}
        stem = facets.stem_text(legacy_problem)
        self.assertFalse(facets.matches_all(stem, ["算术"]))

    def test_the_source_domain_reads_evidence_year_and_the_leading_tags(self):
        source = facets.source_text(self.PROBLEM)
        for word in ("final·a", "2023-2024秋冬", "【2023期末】", "合集a"):
            self.assertTrue(facets.matches_all(source, [word.casefold()]), word)
        for word in ("计数原理", "1+2+3"):
            self.assertFalse(facets.matches_all(source, [word.casefold()]), word)

    def test_tags_only_count_at_the_head_of_the_text(self):
        self.assertEqual(
            facets.source_text({"problem_text": "计算 1+2+3，然后【补充说明】"}),
            "",
        )


if __name__ == "__main__":
    unittest.main()
