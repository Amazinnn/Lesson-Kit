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
                     "source_evidence": "题库/midterm·A.md 第1题"},
                    {"source_kind": "midterm", "exam_year": "2024-2025秋冬",
                     "source_evidence": "题库/midterm·A.md 第2题"},
                    {"source_kind": "final", "exam_year": None,
                     "source_evidence": "教材 第3章"},
                    {"source_kind": None, "exam_year": None, "source_evidence": None},
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


if __name__ == "__main__":
    unittest.main()
