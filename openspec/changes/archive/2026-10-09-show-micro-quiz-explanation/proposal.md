## Why

On the practice page, clicking 查看解析 for a micro-quiz item shows only the
answer key and a one-line `error_reason` (437 of 458 are under 40 characters,
mean 11), while the problem's own `solution` — a written explanation of 250+
characters that exists for 494 of 497 pool items — is never displayed. The
learner sees a verdict and no explanation. The current spec mandates this:
"Session-end rating cards SHALL show the micro-quiz answer key and error reason
**instead of a formal solution**", so the detail exists in the pool but the
contract hides it.

## What Changes

- Micro-quiz reveal (查看解析) and session-end rating cards now also render the
  problem's stored `solution` when non-empty, alongside the answer key and
  error reason, labelled by `solution_origin` (`AI 生成解析` / `教材解析` /
  `解析`), using the same explanation section the exam flow already shows.
- Keyless items keep their "no stored answer key" notice; items with no stored
  `solution` fall back to key + error reason only. Items without a
  micro-quiz payload render exactly as before.
- No data changes: this change does **not** backfill the 109 keyless items,
  the 3 items with empty `solution`, or expand the short `error_reason`
  strings, and it does not append the `source_answer` file-path evidence to
  the quiz branch (it is ingest provenance, not a learner-facing answer).
- A single shared explanation-section renderer is reused by the exam and quiz
  reveal paths so both flows present identical markup.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `micro-quiz-content`: requirement **Type-aware practice rendering** —
  reveal and session-end rating cards additionally show the problem's stored
  written solution (labelled by origin) instead of suppressing it; keyless
  and solution-less fallbacks are spelled out.

## Impact

- Code: `workbench/server/static/practice-flow.js` (shared explanation
  section helper; two quiz branches — per-item reveal and batch/off-mode
  rating card).
- Tests: `tests/workbench/workbench_ui_interactions.test.js` (existing
  reveal test updated, new explanation test added).
- No server, API, pool, or ingest change; purely front-end presentation of
  data already stored on the problem row.
