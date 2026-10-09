"""Pure, body-only typesetting measurements and factual advisory reports."""

import copy
import json
import unittest

try:
    from workbench.domain import typesetting
except ImportError:
    typesetting = None


class TypesettingTests(unittest.TestCase):
    def check(self, rows, **kwargs):
        self.assertIsNotNone(typesetting, "shared typesetting rule is missing")
        return typesetting.check(rows, **kwargs)

    def test_inclusive_boundaries_and_zero_visible_exception(self):
        rows = [{"kp_id": f"kp-{n}", "body": "字" * n}
                for n in (0, 39, 40, 300, 301)]
        report = self.check(rows)
        self.assertEqual([r["kp_id"] for r in report["short"]], ["kp-39"])
        self.assertEqual([r["kp_id"] for r in report["over_long"]], ["kp-301"])
        self.assertEqual(report["band"], {"min": 40, "max": 300})
        self.assertEqual(report["summary"]["paragraphs"], 4)
        self.assertEqual(report["summary"]["short"],
                         {"knowledge_points": 1, "share": 0.2})

    def test_math_and_code_are_removed_for_measurement_only(self):
        rows = [{"key": "kp", "body": "字" * 40 + "\n\n$$x^2$$\n\n$x$\n\n`code`"}]
        before = copy.deepcopy(rows)
        report = self.check(rows)
        self.assertEqual(rows, before)
        self.assertEqual(report["short"], [])
        self.assertEqual(report["over_long"], [])
        self.assertEqual(report["summary"]["paragraphs"], 4)
        self.assertEqual(report["summary"]["visible_characters"],
                         {"p50": 0, "p75": 0, "p90": 40, "p99": 40})
        mixed = self.check([{"key": "kp", "body": "a" * 39 + "$formula$`code`b"}])
        self.assertEqual(mixed["short"], [])

    def test_fenced_code_and_display_math_across_blank_lines_have_zero_count(self):
        body = "字" * 40 + "\n\n```python\nx = 1\n\n# note\n```\n\n$$\nx\n\n+y\n$$"
        report = self.check([{"key": "kp", "body": body}])
        self.assertEqual(report["short"], [])
        self.assertEqual(report["over_long"], [])
        self.assertEqual(report["summary"]["paragraphs"], 5)

    def test_blank_line_split_crlf_and_body_only_language_neutral_count(self):
        for char in ("a", "字"):
            with self.subTest(char=char):
                report = self.check([{"key": "kp", "body": char * 40 + "\r\n \t\r\n" + char * 300,
                                      "fragile": "x", "learning_action": "x" * 301}])
                self.assertEqual(report["summary"]["paragraphs"], 2)
                self.assertEqual(report["short"], [])
                self.assertEqual(report["over_long"], [])
                self.assertEqual(report["summary"]["visible_characters"]["p50"], 40)

    def test_both_bounds_appear_once_and_over_long_is_rendered_first(self):
        report = self.check([
            {"key": "short-only", "body": "a"},
            {"key": "both-sides", "body": "x" * 301 + "\n\n" + "x" * 12},
        ])
        self.assertEqual(report["over_long"], [{
            "kp_id": "both-sides", "over_long_paragraphs": 1, "short_paragraphs": 1,
            "min_visible_characters": 12, "max_visible_characters": 301,
        }])
        self.assertEqual([r["kp_id"] for r in report["short"]], ["short-only"])
        self.assertEqual(report["summary"]["short"],
                         {"knowledge_points": 2, "share": 1.0})
        rendered = typesetting.render_text(report)
        self.assertEqual(rendered.count("both-sides"), 1)
        self.assertLess(rendered.index("both-sides"), rendered.index("short-only"))
        self.assertIn("over 300: 1", rendered)
        self.assertIn("under 40: 1", rendered)
        self.assertIn("min 12, max 301", rendered)
        for prohibited in ("target", "recommended", "split point", "template"):
            self.assertNotIn(prohibited, rendered.lower())
        json.dumps(report)

    def test_nearest_rank_percentiles_not_interpolation(self):
        report = self.check([{"key": "kp", "body": "\n\n".join("x" * n for n in (1, 2, 3, 4))}])
        self.assertEqual(report["summary"]["visible_characters"],
                         {"p50": 2, "p75": 3, "p90": 4, "p99": 4})

    def test_missing_input_is_distinct_from_checked_clean_empty(self):
        missing = self.check([], available=False)
        clean = self.check([])
        self.assertFalse(missing["available"])
        self.assertTrue(clean["available"])
        self.assertNotEqual(typesetting.render_text(missing), typesetting.render_text(clean))
        self.assertIn("no input available", typesetting.render_text(missing))
        self.assertEqual(clean["summary"]["visible_characters"],
                         dict.fromkeys(("p50", "p75", "p90", "p99")))
        self.assertEqual(clean["summary"]["short"]["share"], 0)
        self.assertNotIn("Over-long paragraphs", typesetting.render_text(clean))
        self.assertNotIn("Short paragraphs", typesetting.render_text(clean))
