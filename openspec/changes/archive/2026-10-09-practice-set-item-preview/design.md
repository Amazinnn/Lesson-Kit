# Design notes

## `<details>`, not a modal, not a route

The page already renders every item server-side and reloads on reorder, so the
preview has to survive a reload without new state. A native `<details>` gives
open/closed per item for free — no JavaScript, no new endpoint, no stored
preference — and it survives `reloadPage()` in whatever state the learner left
it in after the reload (collapsed, which is the honest default for a list of
titles). A modal or a `/practice-sets/{id}` detail route would need the pool
read again, a fetch path, and an escape route; the page already holds everything
the preview shows.

## Buttons stay outside the `<summary>`

Activating anything inside a `<summary>` toggles the block. The ↑ / ↓ / 移除
controls therefore stay siblings of the `<details>`, not children: pressing 移除
must remove an item, never open a preview. This also keeps the existing click
delegation intact — it looks for `button.closest(".practice-set-item")`, and the
`<li data-problem-id>` wrapper is unchanged.

## The disclosure marker is drawn

`display: grid` on a `<summary>` suppresses the browser's triangle (the marker
only renders for `list-item`), and the row needs a grid so the index stays a
column. The affordance is therefore drawn: `::before` carries `▸` / `▾` in a
14px first column, so every item shows — without hovering — that it opens.

## The card folds with the same element it teaches

The item previews are `<details>`, so the card uses one too: the head (title,
size, controls) is the summary and the problem list is the content. No toggle
button, no `hidden` class juggling, no second mechanism to explain.

The head holds the paper's controls, and a click inside a `<summary>` would
normally toggle it — so the existing delegated click handler calls
`event.preventDefault()` once it knows the target is a button. That is the whole
client difference: a control click is consumed by the control.

## The fold is remembered per tab, not stored anywhere

Every edit (move, remove) reloads the page, and a reload would fold the card the
learner is working in — three moves would mean re-opening the paper three times.
The open/closed state therefore lives in `sessionStorage` under
`wb_paper_open_<workspace>`, exactly like the practice page's filter state: it
dies with the tab, it is never sent anywhere, and it is never a fact about the
paper. Reading it costs one `load()`; the `toggle` event writes it back. Nested
item folds bubble their `toggle` too, so the handler ignores events whose target
is not the card body.

## Head layout: flex, with a drawn marker

The head was already a flex row (title block + actions). It stays one; the
disclosure marker is the first flex item, drawn with `::before` because
`display: flex` suppresses the native triangle. The title block gets
`flex: 1 1 auto` so `space-between` still parks the controls on the right and the
problem list keeps the card's full width — a grid across the card would squeeze
the list beside the buttons.

## The body is the knowledge point page's body

`linked-problem-text rich-text` fed by `_render_markdown` is exactly what the
knowledge point page shows for the same problems, so a formula, a figure, or a
code block renders the same on both surfaces and there is one Markdown subset to
keep safe. The preview carries the stem and the recorded source line — never the
solution: a saved paper is usually about to be practised, and the export button
already produces the answer sheet for when the learner wants it.

`_render_markdown` takes a `kp_id` it no longer reads (the figure path is
resolved from the workspace name alone), so the paper card passes an empty
string rather than inventing a knowledge point for a problem that may carry
several.

## Collapsed is the default, and it is also the contract

A 77-problem paper must stay scannable: the card folds to its head, and the item
list is a table of contents until the learner opens one line. Nothing about the
paper changes when either fold moves — the `<li>` order, the ids sent to
`PATCH`, and the rendered paper are all untouched. The card's status line (the
place a failed rename/export reports itself) sits outside the fold, so an error
is visible on a folded card instead of hidden inside it.

## Verification

- `tests/workbench/test_ui_routes.py`: the saved-paper page test asserts the
  expandable body, the preview text of the paper's problem, and that the
  reorder/remove controls are still present.
- `python -m pytest tests -q`, `node --test tests/workbench/*.test.js`,
  `openspec validate --strict`.
- Live check on a real workspace: `/w/<name>/practice-sets` renders both saved
  papers, each item opens to its problem, the paper's 77 items still collapse.
