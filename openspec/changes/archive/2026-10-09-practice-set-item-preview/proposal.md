## Why

A saved paper on the 组卷 page lists its problems by title alone: one `<li>` per
item holding an index, a title, and three buttons. The page answers "which
problems are in this paper" but not "what do they say" — and a learner assembles
a paper precisely to read it. Nothing on the page carries the text either:
`practice_sets_page` never renders `problem_text`, and the only surface that
shows a problem's own words is the knowledge point page's linked-problem list.
So the one page that manages a paper cannot show a single line of its contents,
and reading your own selection means exporting Markdown to a file viewer.

**And the card was the whole list.** A page holding two papers rendered every
problem both of them hold — 150 rows — so reaching the second paper meant
scrolling past the first one's entire contents. The page is a list of papers;
it was rendering a pile of problems.

## What Changes

- **Every item of a saved paper becomes an expandable block.** The summary keeps
  the row as it is today (index, title, ↑ / ↓ / 移除); opening it reveals the
  problem's full text and its recorded source line.
- **Every card folds as a whole.** The head — title, size, controls — is the
  fold's summary and stays visible; the problem list folds away beneath it.
  Cards arrive folded, so a page holding a 77-problem paper and a 73-problem
  paper reads as two lines of paper, not 150 rows of problems.
- **An opened card survives the reload an edit performs.** The fold is
  remembered per tab (the same session-scoped, per-workspace storage the
  practice page's filters already use), so moving three problems in a row does
  not mean opening the paper three times.
- **The head's controls do not fold the card.** A control click is consumed by
  the control: 导出 exports, 开始练习 starts, and the fold stays put.
- **The body reuses the existing rendering path.** `_render_markdown` plus the
  `linked-problem-text rich-text` surface — the exact pair the knowledge point
  page uses for the same problems, so math, figures and code render the same on
  both surfaces.
- **Nothing else changes.** No new data, endpoint, or paper format: the rows keep
  their `<li data-problem-id>`, so reordering/removal continues to work on
  titles while previews open and close independently.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: the 组卷 page's saved-paper items gain an in-place preview of
  the problem they name.

## Impact

- **Code**: `workbench/server/pages.py` (`practice_sets_page` item and card
  markup), `workbench/server/static/workbench.css` (item row, card head, drawn
  disclosure markers), `workbench/server/static/workbench.js` (fold memory,
  control clicks consumed by the control).
- **Tests**: `tests/workbench/test_ui_routes.py` — the saved-paper page test
  asserts both folds; `tests/workbench/workbench_ui_interactions.test.js` — the
  fold is restored and remembered per tab.
- **Docs**: changelog entries; `docs/PRODUCT-MANUAL.md` gains the one section
  the 组卷 page was missing.
- **Not touched**: the paper data contract (`ps-NNN`, `.lessonkit/practice-sets/`),
  the routes, and the CLI.
