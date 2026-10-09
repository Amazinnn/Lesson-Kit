## 1. Diagnose

- [x] 1.1 Confirm the residual-answer symptom lives in the practice-page
  reveal panel, not in pool data (user confirmation via AskUserQuestion)
- [x] 1.2 Measure pool content read-only: 494/497 problems carry a detailed
  `solution`, 458 have `micro_quiz`, 437/458 `error_reason` under 40 chars,
  109 keyless, 3 empty solutions
- [x] 1.3 Fix scope confirmed with user: UI-only, no data backfill, no
  `source_answer` block in the quiz branch

## 2. Implementation

- [x] 2.1 Add `practiceExplanationSection(problem)` (origin label from
  `solution_origin`, `""` when `solution` empty) and reuse it from
  `practiceSolutionHtml` in `workbench/server/static/practice-flow.js`
- [x] 2.2 Append the explanation section to the micro-quiz reveal branch
  (查看解析)
- [x] 2.3 Append the explanation section to the batch/off-mode rating-card
  quiz branch

## 3. Tests

- [x] 3.1 Update the existing reveal test to assert key + reason shown and
  no explanation section when the row has none
- [x] 3.2 Add a test asserting reveal of a micro quiz with a stored
  `solution` includes the explanation section

## 4. Verification

- [x] 4.1 `node --test tests/workbench/workbench_ui_interactions.test.js`
  (98 pass)
- [x] 4.2 `node --test tests/workbench/agent_session_ui.test.js` (3 pass)
- [x] 4.3 `python -m pytest tests/workbench/test_ui_routes.py -q`
  (66 passed)

## 5. OpenSpec change

- [x] 5.1 Write `proposal.md`
- [x] 5.2 Write the `micro-quiz-content` spec delta (MODIFIED
  "Type-aware practice rendering", full requirement copied and edited)
- [x] 5.3 Write `design.md`
- [x] 5.4 Write `tasks.md`
- [x] 5.5 `openspec validate show-micro-quiz-explanation` passes
