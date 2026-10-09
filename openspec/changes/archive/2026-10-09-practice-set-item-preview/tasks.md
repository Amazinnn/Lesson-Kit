# Tasks

All items are done in this change; the list is the record of what was touched.

## 1. Page markup

- [x] 1.1 `workbench/server/pages.py`: `practice_sets_page` wraps each item's
  index + title in `<details class='practice-set-item-body'><summary>`
- [x] 1.2 the opened body renders `problem_text` through `_render_markdown`
  into `linked-problem-text rich-text`, plus the recorded source line
- [x] 1.3 the ↑ / ↓ / 移除 controls stay outside the `<details>`; the
  `<li class='practice-set-item' data-problem-id>` wrapper is unchanged

## 2. Styling

- [x] 2.1 `workbench/server/static/workbench.css`: `.practice-set-item` becomes
  a two-column grid (body, actions) aligned to the top so an open preview does
  not centre the controls against a tall body
- [x] 2.2 the summary lays out the drawn marker, the index column and the title;
  `[open]` flips the marker
- [x] 2.3 `.practice-set-card-head` stays a flex row, gains the drawn marker and
  `cursor: pointer`; `.practice-set-card-title` takes `flex: 1 1 auto` so the
  controls stay right-aligned and the folded list keeps the full card width

## 2b. Card fold

- [x] 2b.1 `workbench/server/pages.py`: the card becomes
  `<details class='practice-set-card-body'><summary class='practice-set-card-head'>`
  holding the title block and the controls; the item list and the fold's content
  sit below it
- [x] 2b.2 the status line moves outside the fold so an error stays visible
- [x] 2b.3 `workbench/server/static/workbench.js`: `restorePaperFolds()` restores
  and remembers the open state per tab (`wb_paper_open_<ws>`), ignoring nested
  item toggles
- [x] 2b.4 a control click calls `event.preventDefault()`, so 导出 / 开始练习 do
  not also fold the card

## 3. Tests

- [x] 3.1 `tests/workbench/test_ui_routes.py`: the saved-paper page test asserts
  the expandable body and the problem's own text reaches the page
- [x] 3.2 the same test asserts the card-level fold and that the item list sits
  inside it
- [x] 3.3 `tests/workbench/workbench_ui_interactions.test.js`: a folded card is
  restored open from this tab's storage and remembers being closed
- [x] 3.4 `tests/workbench/test_ui_routes.py`: a folded card's status line stays
  outside the `<details>` so command errors remain visible

## 4. Docs

- [x] 4.1 changelog entry `changelog/2026-10-06-practice-set-item-preview.md`
- [x] 4.2 changelog entry `changelog/2026-10-07-saved-paper-card-fold.md`
- [x] 4.3 `docs/PRODUCT-MANUAL.md`: the 组卷 page's missing section (what a card
  holds, that cards fold, and that items open in place)

## 5. Verification

- [x] 5.1 `python -m pytest tests -q`
- [x] 5.2 `node --test tests/workbench/*.test.js`
- [x] 5.3 `openspec validate --strict`
- [x] 5.4 daemon restarted; a real 77-item paper renders folded, opens and
  remembers the fold
