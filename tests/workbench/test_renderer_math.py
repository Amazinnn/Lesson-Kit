"""Renderer regressions: math escaping, display blocks, emphasis, parity.

Each test here corresponds to a defect confirmed against `pool/ncmc.db` in
`_work/kb/tools/audit/problems-report/06-renderer-code-review.md`:

* A1 the math fragment was HTML-escaped twice, so KaTeX received `a&amp;lt;b`
  and every formula holding `<`, `>` or `'` failed to parse (963 spans).
* A2 `_rich` ran one line at a time, so a `$$` block whose delimiters own
  their own lines never matched and rendered as bare LaTeX (433 blocks).
* A4 the emphasis regexes ate LaTeX-escaped underscores, so a Chinese
  fill-in blank showed backslashes instead of underscores (60 entities).
* A5 the server and the browser were two independent implementations that
  agreed on the fatal defects and diverged on the harmless ones.
"""

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from workbench.server import pages


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "rich_text.json"
WORKSPACE = "dmath"

MATH_SPAN = re.compile(r"<span class='math(?: display)?'>(.*?)</span>", re.DOTALL)


def render_inline(markdown, workspace=WORKSPACE):
    return pages._rich(markdown, workspace)


def render_block(markdown, workspace=WORKSPACE):
    return pages._render_markdown(markdown, workspace, "dmath-ch06-kp-001")


def math_bodies(html):
    return MATH_SPAN.findall(html)


class MathEscapedOnceTests(unittest.TestCase):
    """A1: every math fragment must be escaped exactly once."""

    def test_comparison_inside_math_is_escaped_once(self):
        # The corpus shape behind 963 broken spans: `f'(x)`, `a<b`, `x>0`.
        self.assertIn("<span class='math'>a&lt;b</span>", render_inline("当 $a<b$ 时"))
        self.assertIn("f&#x27;(x)", render_inline("$f'(x)$"))
        self.assertIn("a=&quot;b&quot;", render_inline('$a="b"$'))

    def test_no_fragment_is_escaped_twice(self):
        for markdown in ("$a<b$", "$f'(x)$", '$a="b"$', "$$x<y \\quad f>0$$"):
            with self.subTest(markdown=markdown):
                for body in math_bodies(render_inline(markdown)):
                    self.assertNotIn("&amp;lt;", body)
                    self.assertNotIn("&amp;gt;", body)
                    self.assertNotIn("&amp;quot;", body)
                    self.assertNotIn("&amp;#x27;", body)

    def test_raw_html_inside_math_stays_escaped_text(self):
        html = render_inline("$<img src=x onerror=alert(1)>$")
        self.assertEqual(
            html, "<span class='math'>&lt;img src=x onerror=alert(1)&gt;</span>")
        self.assertNotIn("<img", html)

    def test_ampersand_stays_a_single_escape(self):
        # `&` is legal in `aligned`; it must reach KaTeX as one character.
        self.assertEqual(
            math_bodies(render_inline("$a \\land b$")), ["a \\land b"])
        self.assertEqual(math_bodies(render_inline("$a & b$")), ["a &amp; b"])


class DisplayBlockTests(unittest.TestCase):
    """A2: a `$$` block must render even when it spans several lines."""

    MULTILINE = "试证：\n\n$$\n\\exists x _ {0} \\in [ 0, 1 ]\n$$\n"

    def test_multiline_block_renders_as_display_math(self):
        html = render_block(self.MULTILINE)
        self.assertIn("<span class='math display'>", html)
        self.assertIn("\\exists x _ {0} \\in [ 0, 1 ]", html)
        self.assertNotIn("$$", html)

    def test_several_blocks_in_one_document_all_render(self):
        html = render_block(
            "$$\n\\exists x\n$$\n\n$$\n\\left| f \\right| > 4\n$$\n")
        self.assertEqual(html.count("<span class='math display'>"), 2)
        self.assertNotIn("$$", html)

    def test_a_comparison_inside_a_block_reaches_katex_once(self):
        html = render_block("$$\n\\left| f \\right| > 4\n$$")
        self.assertIn("&gt; 4", html)
        self.assertNotIn("&amp;gt;", html)

    def test_a_block_inside_a_fence_stays_literal_code(self):
        html = render_block("```\n$$\nnot math\n$$\n```")
        self.assertIn("<pre><code>", html)
        self.assertNotIn("<span class='math", html)

    def test_a_block_body_keeps_its_own_blank_lines(self):
        html = render_block("$$\n\\begin{aligned}\na &= b \\\\\nc &= d\n\\end{aligned}\n$$")
        self.assertIn("\\begin{aligned}", html)
        self.assertIn("a &amp;= b \\\\", html)

    def test_single_line_block_still_renders(self):
        html = render_block("$$E = 2k\\lambda / R$$")
        self.assertIn("<span class='math display'>E = 2k\\lambda / R</span>", html)


class EscapedUnderscoreTests(unittest.TestCase):
    """A4: `\\_` outside math is a fill-in blank, not an italic delimiter."""

    def test_four_underscores_render_as_a_blank(self):
        self.assertIn("____.", render_inline(r"\_\_\_\_."))

    def test_a_long_run_of_escaped_underscores_is_all_blank(self):
        self.assertEqual(render_inline(r"\_" * 20), "_" * 20)

    def test_no_em_tag_is_produced_for_a_blank(self):
        self.assertNotIn("<em>", render_inline(r"\_\_\_\_."))

    def test_the_reported_problem_entity(self):
        # ncmc-ch01-prob-012, verbatim from the corpus.
        raw = (r"设 $x_{n} = \sum_{k=1}^{n} \frac{k}{(k+1)!}$ , 则 "
               r"$\lim_{n \to \infty} x_{n} =$ \_\_\_\_.")
        html = render_inline(raw)
        self.assertIn("____.", html)
        self.assertNotIn("<em>", html)
        # No stray backslash may survive OUTSIDE the math spans.
        self.assertNotIn("\\", MATH_SPAN.sub("", html))

    def test_underscores_inside_math_stay_escaped(self):
        # Inside math `_` is a subscript; the escape must survive untouched.
        self.assertEqual(
            math_bodies(render_inline(r"$\sum_{i=1}^{n} x_i$")),
            [r"\sum_{i=1}^{n} x_i"])

    def test_star_escapes_do_not_start_emphasis(self):
        self.assertNotIn("<em>", render_inline(r"$a \* b$"))
        self.assertIn("<span class='math'>a \\* b</span>", render_inline(r"$a \* b$"))

    def test_plain_markdown_emphasis_still_works(self):
        self.assertIn("<em>下划斜体</em>", render_inline("_下划斜体_"))
        self.assertIn("<strong>粗体</strong>", render_inline("**粗体**"))
        self.assertIn("<em>斜体</em>", render_inline("*斜体*"))

    def test_triple_star_nests_properly(self):
        self.assertEqual(
            render_inline("***bold italic***"),
            "<strong><em>bold italic</em></strong>")


class LinkAndImageTests(unittest.TestCase):
    """The report's hardening items: no double escaping, no path traversal."""

    def test_external_link_query_string_survives(self):
        self.assertIn(
            "href='https://e.com/?a=1&amp;b=2'",
            render_inline("[link](https://e.com/?a=1&b=2)"))

    def test_wiki_link_renders_its_label(self):
        self.assertIn(
            "<a href='/w/dmath/kp/kp-01'>级数展开</a>",
            render_inline("见 [[kp-01|级数展开]] 继续"))

    def test_wiki_link_rejects_a_path_traversal_id(self):
        html = render_inline("见 [[../../etc/passwd]] 继续")
        self.assertNotIn("href='/w/dmath/kp/../", html)
        self.assertIn("../../etc/passwd", html)

    def test_image_alt_is_escaped_once(self):
        self.assertIn(
            "<img alt='a&lt;b 图' src='/api/w/dmath/figures/ch12/abc.png'>",
            render_inline("![a<b 图](ch12/abc.png)"))

    def test_image_scheme_is_not_turned_into_a_url(self):
        self.assertNotIn("<img", render_inline("![x](javascript:alert(1))"))

    def test_workspace_name_cannot_break_out_of_the_href(self):
        html = render_inline("[[kp-01|标签]]", workspace="x' onmouseover='alert(1)")
        self.assertNotIn("onmouseover='alert(1)'", html.split(">")[0])


class NestedInlineTokenTests(unittest.TestCase):
    """Stashed math must survive code and link labels without token leakage."""

    def test_inline_code_keeps_single_and_double_math_delimiters_literal(self):
        self.assertEqual(render_inline("`$x$`"), "<code>$x$</code>")
        self.assertEqual(render_inline("`$$x$$`"), "<code>$$x$$</code>")

    def test_fenced_code_keeps_single_and_double_math_delimiters_literal(self):
        self.assertEqual(
            render_block("```\n$x$\n```"), "<pre><code>$x$</code></pre>")
        self.assertEqual(
            render_block("```\n$$x$$\n```"), "<pre><code>$$x$$</code></pre>")

    def test_block_inline_code_keeps_math_literal(self):
        self.assertEqual(render_block("`$x$`"), "<p><code>$x$</code></p>")
        self.assertEqual(render_block("`$$x$$`"), "<p><code>$$x$$</code></p>")

    def test_backticks_inside_math_are_not_code(self):
        self.assertEqual(render_inline("$a`b`c$"), "<span class='math'>a`b`c</span>")

    def test_external_link_math_labels_are_restored(self):
        self.assertEqual(
            render_inline("[math $x$](https://example.com)"),
            "<a href='https://example.com' target='_blank' "
            "rel='noopener noreferrer'>math <span class='math'>x</span></a>",
        )

    def test_wiki_link_math_labels_are_restored(self):
        self.assertEqual(
            render_inline("[[kp-01|$x$]]"),
            "<a href='/w/dmath/kp/kp-01'><span class='math'>x</span></a>",
        )

    def test_math_in_image_alt_stays_literal_and_preserves_src(self):
        for math in ("$x$", "$$x$$"):
            expected = f"<img alt='image {math}' src='/api/w/dmath/figures/fig.png'>"
            self.assertEqual(render_inline(f"![image {math}](fig.png)"), expected)
            self.assertEqual(render_block(f"![image {math}](fig.png)"), "<p>" + expected + "</p>")

    def test_math_delimiters_in_link_url_stay_literal(self):
        self.assertEqual(
            render_inline("[label](https://example.com/$x$?a=1&b=2)"),
            "<a href='https://example.com/$x$?a=1&amp;b=2' target='_blank' "
            "rel='noopener noreferrer'>label</a>",
        )


class SharedFixtureTests(unittest.TestCase):
    """Every shared fixture case must hold on the server renderer."""

    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_every_case_renders(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["name"]):
                html = render_block(case["markdown"])
                for fragment in case["contains"]:
                    self.assertIn(fragment.replace("{workspace}", WORKSPACE), html)
                for fragment in case["excludes"]:
                    self.assertNotIn(fragment, html)

    def test_the_fixture_covers_the_regression_inputs(self):
        names = {case["name"] for case in self.fixture["cases"]}
        for required in ("inline_math_escapes_once", "display_math_escapes_once",
                         "display_math_spans_lines",
                         "latex_escaped_underscore_is_a_blank"):
            self.assertIn(required, names)


class PythonJavaScriptParityTests(unittest.TestCase):
    """A5: the two renderers must produce equivalent HTML, not merely similar.

    Runs the real `workbench.js` renderer under Node and compares it against
    the real `pages._render_markdown` / `pages._rich` for the same inputs.
    """

    RUNNER = REPO_ROOT / "tests" / "workbench" / "renderer_parity_cases.js"

    CASES = [
        ("inline", "$a<b$"),
        ("inline", "$f'(x)$"),
        ("inline", '$a="b"$'),
        ("inline", "$$x=1 \\tag{1}$$"),
        ("inline", r"\_\_\_\_."),
        ("inline", r"\_" * 20),
        ("inline", r"a_1 + b_2"),
        ("inline", "***bold italic***"),
        ("inline", "**b** and *i*"),
        ("inline", "[link](https://e.com/?a=1&b=2)"),
        ("inline", "[[kp-01|标签]]"),
        ("inline", "[[../../etc/passwd]]"),
        ("inline", "![a<b](fig.png)"),
        ("inline", "![x](javascript:alert(1))"),
        ("inline", "![x](/static/workbench.css)"),
        ("inline", "snake_case_name"),
        ("inline", "`code` $a`b$"),
        ("inline", "`$x$`"),
        ("inline", "`$$x$$`"),
        ("inline", "$a`b`c$"),
        ("inline", "[math $x$](https://example.com)"),
        ("inline", "[[kp-01|$x$]]"),
        ("inline", "[[kp-01|]]"),
        ("inline", "![image $x$](fig.png)"),
        ("inline", "[label](https://example.com/$x$?a=1&b=2)"),
        ("inline", "__bold__ and _em_"),
        ("inline", r"\* star in math"),
        ("inline", "$$x=1$$"),
        ("inline", "sup<sup>2</sup>"),
        ("inline", "$a \\* b$"),
        ("inline", "$a & b$"),
        ("inline", "$a \\land b$"),
        ("inline", "<sup><img src=x onerror=alert(1)></sup>"),
        ("inline", "$<img src=x onerror=alert(1)>$"),
        ("inline", "**结论与公式。** 定理1.24：一切基本初等函数连续。"),
        ("inline", "$f'(0)$ and $g''(x) < 0$"),
        ("inline", r"$a _ {n}$"),
        ("block", "试证：\n\n$$\n\\exists x _ {0} \\in [ 0, 1 ]\n$$\n"),
        ("block", "文字\n$$\nx=1\n$$\n后文"),
        ("block", "```\n$$\nnot math\n$$\n```"),
        ("block", "```\n$x$\n```"),
        ("block", "```\n$$x$$\n```"),
        ("block", "`$x$`"),
        ("block", "`$$x$$`"),
        ("block", "![image $x$](fig.png)"),
        ("block", "![image $$x$$](fig.png)"),
        ("block", "[label](https://example.com/$$x$$)"),
        ("block", "[math $$x$$](https://example.com)"),
        ("block", "[[kp-01|$$x$$]]"),
        ("block", "$$\nE = 2k\\lambda / R\n$$"),
        ("block", "$$\nx=1\n$$"),
        ("block", "| 记号 | 说明 |\n| --- | --- |\n| $a<b$ | **磁** |"),
        ("block", "> 引用 $a<b$"),
        ("block", "空行\n\n$$x=1$$\n\n后面"),
        ("block", "**性质陈述。** 性质1：若 $f,g$ 在 $x_0$ 处连续。"),
    ]

    # Documented, deliberate differences: the fixture exempts heading levels
    # (the server keeps its own <h1>), and the browser emits a code-fence
    # language class the server does not. Neither is a math/text defect.
    KNOWN_DIFFERENCES = ("## ", "```python")

    @classmethod
    def setUpClass(cls):
        cls.javascript = cls._run_javascript()

    @classmethod
    def _run_javascript(cls):
        payload = [{"mode": mode, "in": text} for mode, text in cls.CASES]
        with tempfile.TemporaryDirectory() as staging:
            cases_path = Path(staging) / "cases.json"
            cases_path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                ["node", str(cls.RUNNER), str(cases_path)],
                cwd=REPO_ROOT, capture_output=True, check=False,
            )
        output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
        if result.returncode != 0:
            raise AssertionError("node renderer failed:\n" + output[:4000])
        rendered = {}
        for line in output.splitlines():
            if line.strip():
                item = json.loads(line)
                rendered[(item["mode"], item["in"])] = item["out"]
        return rendered

    def test_the_browser_renderer_answered_every_case(self):
        self.assertEqual(len(self.javascript), len(self.CASES))

    def test_both_renderers_agree_on_every_input(self):
        differences = []
        for mode, text in self.CASES:
            if any(marker in text for marker in self.KNOWN_DIFFERENCES):
                continue
            with self.subTest(mode=mode, text=text):
                server = render_block(text) if mode == "block" else render_inline(text)
                browser = self.javascript[(mode, text)]
                if server != browser:
                    differences.append((mode, text, server, browser))
                self.assertEqual(server, browser)
        self.assertEqual(differences, [], "unexpected Python/JS divergence")


class PlaceholderSafetyTests(unittest.TestCase):
    """A stash placeholder must never be forgeable from body text."""

    def test_a_forged_inline_placeholder_cannot_crash_the_page(self):
        # The old `\x00N\x00` placeholder raised IndexError -> HTTP 500.
        forged = "\ue0105\ue010"
        self.assertEqual(render_inline(forged), forged)

    def test_a_forged_display_placeholder_cannot_crash_the_page(self):
        forged = "\ue0000\ue000"
        self.assertEqual(render_block(forged), "<p>%s</p>" % forged)


if __name__ == "__main__":
    unittest.main()
