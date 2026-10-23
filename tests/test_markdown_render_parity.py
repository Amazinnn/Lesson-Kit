"""Markdown renderer parity: the server and the browser must emit one HTML.

The server renders knowledge bodies (`workbench/server/pages.py:_render_markdown`)
and the browser renders question stems, solutions, answers, review notes and
chat messages (`workbench/server/static/workbench.js:richText`, injected as
`deps.richText` into `practice-flow.js` / `paper-practice.js`). The two sides
implement the same small safe Markdown subset, but they are two independent
implementations, so they drifted apart.

This module locks them together with a character-exact comparison: the same
corpus is rendered by `pages._render_markdown()` and by the real `workbench.js`
renderer — executed under Node against the shipped source, not a copy — and the
two HTML strings must be equal character by character. No "keep them in sync
by hand" allowance exists here: a divergence is a red test.

Corpus coverage (openspec/changes/workbench-visual-language-v2/tasks.md 7.3,
design.md D-6):
  * three heading levels (`#`, `##`, `###`)
  * fenced code, with and without a language tag
  * block quotes, including quotes whose `>` is indented
  * ordered and unordered lists
  * GFM tables
  * thematic breaks
  * inline math

Recorded pre-refactor differences (this test was red first; design.md D-6
calls them "an existing contract that was never honoured"):

  1. heading levels — server emitted h2/h3/h4 (`#` -> h2), the browser emitted
     h1/h2/h3, so the same body jumped one level between pages.
  2. code fence language — the browser kept `class='language-xx'`, the server
     dropped it (`pages.py` used to lose the language tag).
  3. block quotes — the browser used `/^\\s*>\\s?/`, the server used
     `line.startswith(">")`, so an indented `>` stayed a paragraph on the
     server; and the server stripped every space after `>` where the browser
     strips exactly one.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workbench.server import pages


REPO_ROOT = Path(__file__).resolve().parents[1]
# The Node runner lifts the renderer out of the shipped `workbench.js` source
# and runs it in a `vm` context, so the client side of every assertion below
# is the file that ships, not a copy of it.
RUNNER = REPO_ROOT / "tests" / "workbench" / "renderer_parity_cases.js"
WORKSPACE = "dmath"
KP_ID = "dmath-ch06-kp-001"


# One corpus, one name per feature, so a red test names the feature.
CORPUS = (
    ("heading level 1", "# 一级标题\n正文"),
    ("heading level 2", "## 二级标题\n正文"),
    ("heading level 3", "### 三级标题\n正文"),
    ("heading closed with hashes", "## 标题 ##\n正文"),
    ("code fence without a language", "```\nprint(1)\n```"),
    ("code fence with a language", "```python\nprint(1)\n```"),
    ("code fence with a hyphenated language", "```objective-c\nint a = 1;\n```"),
    ("code fence indented", "  ```python\n  x = 1\n  ```"),
    ("blockquote", "> 引用行"),
    ("blockquote indented by spaces", "  > 行首带空格的引用"),
    ("blockquote indented by three spaces", "   > 三个空格的引用"),
    ("blockquote with several spaces after the marker", ">   引用内容"),
    ("unordered list", "- 第一项\n- 第二项"),
    ("ordered list", "1. 第一步\n2. 第二步"),
    ("ordered list with a closing bracket", "1) 第一步\n2) 第二步"),
    ("list type switch", "- 无序\n\n1. 有序"),
    ("gfm table", "| 量 | 单位 |\n| --- | --- |\n| E | N/C |"),
    ("gfm table with alignment", "| 左 | 右 |\n| :-- | --: |\n| 1 | 2 |"),
    ("thematic break of dashes", "上文\n\n---\n\n下文"),
    ("thematic break of stars", "上文\n\n***\n\n下文"),
    ("inline math", "电荷 $q = 2$ 受力"),
    ("inline math with a comparison", "当 $a<b$ 时"),
    ("display math", "$$\nE = mc^2\n$$"),
    (
        "one document holding every feature",
        "# 知识点标题\n"
        "\n"
        "## 推导\n"
        "\n"
        "### 结论\n"
        "\n"
        "题干：电荷 $q = 2$ 受力。\n"
        "\n"
        "> 引用的定理\n"
        "\n"
        "  > 缩进的引用\n"
        "\n"
        "- 要点一\n"
        "- 要点二\n"
        "\n"
        "1. 第一步\n"
        "2. 第二步\n"
        "\n"
        "| 量 | 单位 |\n"
        "| --- | --- |\n"
        "| E | N/C |\n"
        "\n"
        "```python\nprint(1)\n```\n"
        "\n"
        "```\nprint(2)\n```\n"
        "\n"
        "---\n"
        "\n"
        "结束语。\n",
    ),
)

_BROWSER_OUTPUT = {}


def require_node():
    """Skip loudly — and only loudly — when Node cannot run the browser half."""
    if not RUNNER.exists():
        raise unittest.SkipTest(
            f"Node runner missing: {RUNNER} — the browser half of the "
            f"parity check cannot run without it.")
    if shutil.which("node") is None:
        raise unittest.SkipTest(
            "Node.js is not on PATH — the browser half of the parity check "
            "needs Node to run the shipped workbench.js renderer. Parity was "
            "NOT verified in this environment; install Node, or run the "
            "documented fallback (node unit test + pytest golden samples), "
            "before trusting the two renderers.")


def render_in_browser(texts):
    """Render each text with the shipped `workbench.js` renderer under Node."""
    missing = [text for text in texts if text not in _BROWSER_OUTPUT]
    if not missing:
        return {text: _BROWSER_OUTPUT[text] for text in texts}
    payload = [{"mode": "block", "in": text} for text in missing]
    with tempfile.TemporaryDirectory() as staging:
        cases_path = Path(staging) / "cases.json"
        cases_path.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            ["node", str(RUNNER), str(cases_path)],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    if result.returncode != 0:
        raise AssertionError("node renderer failed:\n" + output[:4000])
    for line in output.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        _BROWSER_OUTPUT[item["in"]] = item["out"]
    return {text: _BROWSER_OUTPUT[text] for text in texts}


def render_on_the_server(markdown):
    return pages._render_markdown(markdown, WORKSPACE, KP_ID)


def first_difference(left, right):
    """Where two strings part company, plus the characters around it."""
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    start = max(0, index - 40)
    return (
        f"first difference at character {index} "
        f"(server length {len(left)}, browser length {len(right)})\n"
        f"  server : ...{left[start:index + 40]!r}\n"
        f"  browser: ...{right[start:index + 40]!r}"
    )


class MarkdownRenderParityTests(unittest.TestCase):
    """The two Markdown renderers must produce the same HTML, byte for byte."""

    @classmethod
    def setUpClass(cls):
        require_node()
        cls.browser = render_in_browser([text for _, text in CORPUS])

    def test_the_browser_renderer_answered_every_case(self):
        self.assertEqual(len(self.browser), len(CORPUS))

    def test_both_renderers_agree_on_every_case(self):
        differences = []
        for name, markdown in CORPUS:
            server = render_on_the_server(markdown)
            browser = self.browser[markdown]
            if server != browser:
                differences.append(
                    f"\n--- {name} ---\n{first_difference(server, browser)}")
        self.assertEqual(differences, [], "".join(differences))

    def test_each_case_is_compared_on_its_own(self):
        # One red case per feature, so a failure names the feature that broke
        # instead of only saying "the corpus diverged somewhere".
        for name, markdown in CORPUS:
            with self.subTest(case=name):
                self.assertEqual(
                    render_on_the_server(markdown),
                    self.browser[markdown],
                    f"{name}: the two renderers disagree",
                )


class UnifiedHeadingLevelTests(unittest.TestCase):
    """7.1: body headings start at h2 on both sides, so the body never
    competes with the page title for h1 (docs/ARCHITECTURE.md:240)."""

    @classmethod
    def setUpClass(cls):
        require_node()
        cls.headings = ("# 标题", "## 标题", "### 标题")
        cls.browser = render_in_browser(cls.headings)

    def test_the_server_keeps_its_h2_start(self):
        self.assertEqual(render_on_the_server("# 标题"), "<h2>标题</h2>")

    def test_the_browser_now_starts_at_h2_as_well(self):
        self.assertEqual(self.browser["# 标题"], "<h2>标题</h2>")

    def test_no_body_heading_reaches_h1(self):
        for markdown in self.headings:
            with self.subTest(markdown=markdown):
                self.assertNotIn("<h1>", self.browser[markdown])


class CodeFenceLanguageTests(unittest.TestCase):
    """7.2: the server keeps the code fence language tag, like the browser."""

    def test_the_server_keeps_the_language_class(self):
        self.assertEqual(
            render_on_the_server("```python\nprint(1)\n```"),
            "<pre><code class='language-python'>print(1)</code></pre>")

    def test_a_fence_without_a_language_stays_plain(self):
        self.assertEqual(
            render_on_the_server("```\nprint(1)\n```"),
            "<pre><code>print(1)</code></pre>")


class BlockquoteRuleTests(unittest.TestCase):
    """7.2: both sides use the browser rule `/^\\s*>\\s?/`."""

    def test_the_server_reads_an_indented_quote_as_a_quote(self):
        self.assertEqual(
            render_on_the_server("  > 缩进的引用"),
            "<blockquote>缩进的引用</blockquote>")

    def test_the_server_keeps_the_spaces_after_the_marker(self):
        # The browser rule strips exactly one space after `>`; the server used
        # to strip all of them, so the two sides disagreed on the text.
        self.assertEqual(
            render_on_the_server(">   引用内容"),
            "<blockquote>  引用内容</blockquote>")


if __name__ == "__main__":
    unittest.main()
