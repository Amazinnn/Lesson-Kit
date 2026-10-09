# Tasks

All items are done in this change; the list is the record of what was touched.

## 1. The trap that started this

- [x] 1.1 `practice-flow.js`: both rating guards (per-problem `#save-rating`,
  session-end card save) reject anything outside 1–5 including NaN
  (`!(rating >= 1 && rating <= 5)`)

## 2. Learner settings

- [x] 2.1 `pages.py::_left_column`: settings section with
  `#setting-show-rating` (「练习与组卷显示自评」, default checked)
- [x] 2.2 `workbench.js`: localStorage-backed `loadSetting`/`saveSetting`
  (`wb_settings_<ws>`); the checkbox round-trips; saved-paper start sends
  `rating_mode: "off" | "immediate"` per the setting
- [x] 2.3 `workbench.css`: settings section styling

## 3. The off round

- [x] 3.1 `practice-flow.js`: `ratingOff()`; the 自评时机 fieldset hides and
  `readyToStart` no longer requires a timing when off
- [x] 3.2 both start paths write `"off"` into `RATING_MODE_KEY` and the
  `POST /practice/current` body
- [x] 3.3 `#next-problem` button (composer actions), visible only in an off
  round once the item is answered; click → `advance()`
- [x] 3.4 the feedback area never renders in an off round; flash cards page via
  `#card-nav` with no rating surface
- [x] 3.5 `finishExhausted` and the resume reload take the no-session-end path
  when off

## 4. Server

- [x] 4.1 `api.py`: `"off"` joins the rating-mode validation sets (paper start,
  active practice)
- [x] 4.2 `records.py`: run label 关闭自评
- [x] 4.3 `attempts.py::record_browser_attempt`: an off-round objective verdict
  derives progress/current-state/schedule (对 → mastered, 错 → wrong) once, no
  rated feedback event; result carries `derived_state`

## 5. Tests

- [x] 5.1 JS: off round start body, no timing required, next-problem advance,
  no feedback surfaces, card paging, localStorage round-trip, empty rating
  rejected inline
- [x] 5.2 Python: `"off"` accepted + labeled, verdict-derived state without a
  rating event, settings section rendered

## 6. Docs & delivery

- [x] 6.1 GLOSSARY (设置、判定折算), PRODUCT-MANUAL (自评时机/左栏/各模式关闭
  分支), REQUIREMENTS, ACTION-GRAPH, changelog
- [x] 6.2 `python -m pytest tests -q`, `node --test tests/workbench/*.test.js`,
  `openspec validate --strict`, compileall
- [x] 6.3 daemon restarted; live round on a real paper: no rating surfaces,
  verdict → solution → 下一题, records show 关闭自评
