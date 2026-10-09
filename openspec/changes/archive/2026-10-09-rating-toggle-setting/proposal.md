## Why

Self-rating is unavoidable today, in three stacked ways. The practice page
requires choosing a rating timing before the first pull (`readyToStart` refuses
otherwise). A saved paper posts an empty body to `start`, so the server defaults
it to `immediate` — the learner never chose anything. And in per-problem mode
the only exits from a problem are `记录并下一题` (rating) and `不会，下一题`
(stuck); the verdict a learner already earned by answering does not move
anything.

The learner preparing for an exam, grinding through knowledge points, does not
want to grade themselves between every problem — and for objective items the
machine has already judged the answer, so the self-question "did I get it?" is
answered by the submission itself. Rating stays valuable where there is no
verdict (subjective problems, flash cards' self-honesty) and for those who want
it; it should not be a wall.

While building this, the trap the learner actually hit surfaced: the rating
input's client guard `rating < 1 || rating > 5` passes for `NaN`, so an empty
input reached the server and died as `rating or note is required` — the round
looked permanently stuck.

## What Changes

- **左栏「设置」区块。** `_left_column` gains a settings section whose first
  entry is one checkbox, 「练习与组卷显示自评」 (`#setting-show-rating`), default
  checked = today's behavior. Stored per workspace under `wb_settings_<ws>` in
  `localStorage` — the first localStorage use in the workbench (all other state
  is session-scoped on purpose; a preference should outlive the tab).
- **`rating_mode` grows `"off"`, end to end.** The practice start body and the
  saved-paper start carry it; `active_practice` / `practice_runs` store it;
  records labels it 关闭自评. No client-side pretending: the stored round
  honestly says what it was.
- **The off round never shows rating.** The 自评时机 fieldset is hidden and not
  required to start; the feedback panel never appears; `finishExhausted` takes
  the immediate cleanup path (no session-end); the resume reload never
  redirects there. Flash cards page freely through the existing card navigation
  with no rating surface and no learning writes.
- **「下一题」 instead of 记录并下一题.** After a problem is submitted (verdict
  rendered for objective items), a `#next-problem` button appears; clicking it
  advances. Nothing auto-advances — the learner reads the solution, then moves.
  The attempt itself is already recorded at submit time.
- **Verdict-derived learning state in off rounds.** When the active round's
  rating mode is off and an objective attempt carries a verdict, the server
  derives the conclusion: 对 → `mastered`, 错 → `wrong` (the same statuses
  `RATING_PROGRESS` produces), current state and schedule follow. Skip still
  marks stuck. No `feedback_events` row with a rating is written — 平均自评 and
  the 1–5 distribution count real self-ratings only. Subjective problems record
  the attempt and derive nothing.
- **The empty-rating trap is fixed** at both rating guards (per-problem and
  session-end): `!(rating >= 1 && rating <= 5)` rejects `NaN` inline.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: the left rail's settings section; the per-problem rating
  surfaces become conditional on the setting.
- `review-workbench`: the practice session's rating-timing requirement becomes
  optional, and an off round's objective verdict is a learning conclusion.

## Impact

- **Code**: `workbench/server/pages.py` (left rail), `workbench/server/static/
  workbench.js` (settings store, paper start body), `workbench/server/static/
  practice-flow.js` (off branches, next-problem, NaN guards),
  `workbench/server/static/workbench.css` (settings section, next-problem),
  `workbench/server/api.py` (`"off"` in the rating-mode validation sets),
  `workbench/server/records.py` (label), `workbench/data/attempts.py`
  (verdict-derived state).
- **Tests**: JS — off round requests, next-problem advance, flash-card paging,
  localStorage persistence, empty-rating inline rejection; Python — `"off"`
  accepted and labeled, verdict-derived progress/schedule with no rating event,
  settings section rendered.
- **Docs**: GLOSSARY (设置、判定折算), PRODUCT-MANUAL (自评时机、左栏、各模式
  的关闭分支), REQUIREMENTS, ACTION-GRAPH, changelog.
- **Not touched**: the agent attempt contract, immediate/batch behavior, the
  session-end page itself, the feedback API.
