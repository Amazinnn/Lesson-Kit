"""Server-side half of the shared safe rich-text fixtures (TDD: red first)."""

import json
import unittest
from pathlib import Path

from workbench.server import pages


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "rich_text.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ServerRichTextParityTests(unittest.TestCase):
    """Linked-problem and knowledge-body Markdown must match the browser subset."""

    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()

    def render(self, markdown):
        return pages._render_markdown(
            markdown, self.fixture["workspace"], "dmath-ch06-kp-001"
        )

    def fragments(self, case):
        # `{workspace}` stands for the owning workspace name.
        return [item.replace("{workspace}", self.fixture["workspace"])
                for item in case["contains"]]

    def test_every_fixture_case_renders_on_the_server(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["name"]):
                html = self.render(case["markdown"])
                for fragment in self.fragments(case):
                    self.assertIn(fragment, html)
                for fragment in case["excludes"]:
                    self.assertNotIn(fragment, html)

    def test_a_table_after_a_paragraph_stays_a_table(self):
        html = self.render("先看表：\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n后文")
        self.assertEqual(html.count("<table"), 1)
        self.assertIn("<p>先看表：</p>", html)
        self.assertIn("<p>后文</p>", html)

    def test_a_two_line_pipe_block_is_not_a_table(self):
        # No delimiter row: this is ordinary prose, not a GFM table.
        html = self.render("| a | b |\n| 1 | 2 |")
        self.assertNotIn("<table", html)
        self.assertIn("| a | b |", html)

    def test_a_code_fence_keeps_its_pipes_literal(self):
        html = self.render("```\n| a | b |\n| --- | --- |\n```")
        self.assertNotIn("<table", html)
        self.assertIn("| a | b |", html)


if __name__ == "__main__":
    unittest.main()
