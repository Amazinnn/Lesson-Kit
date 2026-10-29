## 1. Terminology

- [ ] 1.1 Rename user-visible Chinese 「自评」 → 「评价」 in `workbench/server/pages.py`, `static/practice-flow.js`, `static/paper-practice.js`, `server/records.py`, `domain/mastery.py`, `static/assets/preview.html`, and UI tests.
- [ ] 1.2 Rename the live docs: `docs/GLOSSARY.md` (term + old-name alias), `docs/PRODUCT-MANUAL.md` (including §7.4 heading → 学习状态词汇), `docs/REQUIREMENTS.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/ACTION-GRAPH.md`, and `docs/action-graph/L1-L4`.
- [ ] 1.3 Rename Chinese copy in live specs; update active-change final copy where it is a live contract. Leave archive, changelog, audits, status snapshots, and historical discussion records untouched.
- [ ] 1.4 Grep gate: remaining 「自评」 hits are only historical files or other meanings (`自我评价`, `难度评价`).

## 2. Evaluation CRUD

- [ ] 2.1 Add `workbench/data/pool.py` helpers for reading one event by id, listing events, updating rating/note, and deleting a row.
- [ ] 2.2 Add `workbench/data/evaluations.py` with `list_events`, `get_event`, `add_event`, `update_event`, `delete_event`, expected-value validation, and duplicate-attempt refusal.
- [ ] 2.3 `update_event` / `delete_event` accept any writer and item type; both require expected rating/note; mismatch returns a conflict with zero writes.
- [ ] 2.4 `update_event` changes only `feedback_events.rating/note`; `delete_event` hard-deletes only that row; neither replays projections.
- [ ] 2.5 `add_event` supports optional `attempt_id`; refuse a second evaluation for the same attempt and return the existing event id.
- [ ] 2.6 Extend `lesson-kit feedback` to `add/list/get/update/delete` with backward-compatible default `add`; print JSON for read/update/delete and keep `add`'s text output.
- [ ] 2.7 `feedback get/list` expose `event_id`, `item_type`, `item_id`, `rating`, `note`, `attempt_id`, `created_at`, `agent_recorded`, `correctable`.

## 3. Agent prompts and contracts

- [ ] 3.1 Update `workbench/bridge/agent_contracts.py` `attempts` topic with the evaluation commands, expected-value rule, hard-delete/no-replay boundary, and Agent-chosen rating.
- [ ] 3.2 Update `workbench/bridge/conversations.py::_prompt` topic description to `attempts（记录/更正作答与评价）` and add the read-before-modify line.
- [ ] 3.3 Update `TASK_ROUTER.md` with evaluation list/get/update/delete routing.
- [ ] 3.4 Update `docs/PRODUCT-MANUAL.md` chapter 8 with the same-row edit rule and the score-ownership change.

## 4. Tests

- [ ] 4.1 Agent edits and deletes a browser-written problem evaluation.
- [ ] 4.2 Agent edits and deletes an Agent-written problem evaluation without redirecting to `attempts correct`.
- [ ] 4.3 Expected rating/note mismatch → conflict and zero writes; missing expected values → error.
- [ ] 4.4 Note-only (`rating=none`) evaluations can be edited and deleted.
- [ ] 4.5 kp and card evaluations can be edited and deleted.
- [ ] 4.6 Agent chooses a rating without a learner-supplied value.
- [ ] 4.7 `add --attempt-id` refuses a duplicate and returns the existing event id.
- [ ] 4.8 Legacy `feedback <ws> --item ... --id ... --rating ...` still works.
- [ ] 4.9 Browser stale edit after an Agent edit still returns the existing conflict.
- [ ] 4.10 UI copy assertions use 「评价」.

## 5. Verification

- [ ] 5.1 `python -m pytest tests -q`
- [ ] 5.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`
- [ ] 5.3 `openspec validate --specs --strict`
- [ ] 5.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`
- [ ] 5.5 CLI smoke: `feedback get`, `update` with expected values, `delete`, stale conflict.
- [ ] 5.6 Grep gate for 「自评」 and prompt-contract assertion.
