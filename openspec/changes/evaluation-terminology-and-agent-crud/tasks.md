## 1. Terminology

- [x] 1.1 Rename user-visible Chinese 「自评」 → 「评价」 in `workbench/server/pages.py`, `static/practice-flow.js`, `static/paper-practice.js`, `server/records.py`, `domain/mastery.py`, `static/assets/preview.html`, and UI tests.（实现/文档/测试已在当前树核对）
- [x] 1.2 Rename the live docs:
  （2026-11-09 复核完成：GLOSSARY 词条带旧称「自评」alias；PRODUCT-MANUAL §7.4 标题已是
  「学习状态词汇」，正文残留 1 处已改「评价」；REQUIREMENTS/DATA_MODEL/ARCHITECTURE/
  ACTION-GRAPH/L1-L4 grep 零命中——早已改净） `docs/GLOSSARY.md` (term + old-name alias), `docs/PRODUCT-MANUAL.md` (including §7.4 heading → 学习状态词汇), `docs/REQUIREMENTS.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/ACTION-GRAPH.md`, and `docs/action-graph/L1-L4`.
- [x] 1.3 Rename Chinese copy in live specs;
  （2026-11-09：workbench-ui live spec 两处「关闭自评」改为「关闭评价」对齐 records.py 实际渲染；
  archive/历史记录未动） update active-change final copy where it is a live contract. Leave archive, changelog, audits, status snapshots, and historical discussion records untouched.
- [x] 1.4 Grep gate:
  （2026-11-09：剩余「自评」命中仅 GLOSSARY 旧称 alias 与 _Avoid_ 行、ACTION-GRAPH 2026-10-29
  历史留痕——均为允许类别；gate 已固化为测试 test_terminology_gate.py） remaining 「自评」 hits are only historical files or other meanings (`自我评价`, `难度评价`).

## 2. Evaluation CRUD

- [x] 2.1 Add `workbench/data/pool.py` helpers for reading one event by id, listing events, updating rating/note, and deleting a row.（实现/文档/测试已在当前树核对）
- [x] 2.2 Add `workbench/data/evaluations.py` with `list_events`, `get_event`, `add_event`, `update_event`, `delete_event`, expected-value validation, and duplicate-attempt refusal.（实现/文档/测试已在当前树核对）
- [x] 2.3 `update_event` / `delete_event` accept any writer and item type; both require expected rating/note; mismatch returns a conflict with zero writes.（实现/文档/测试已在当前树核对）
- [x] 2.4 `update_event` changes only `feedback_events.rating/note`; `delete_event` hard-deletes only that row; neither replays projections.（实现/文档/测试已在当前树核对）
- [x] 2.5 `add_event` supports optional `attempt_id`; refuse a second evaluation for the same attempt and return the existing event id.（实现/文档/测试已在当前树核对）
- [x] 2.6 Extend `lesson-kit feedback` to `add/list/get/update/delete` with backward-compatible default `add`; print JSON for read/update/delete and keep `add`'s text output.（实现/文档/测试已在当前树核对）
- [x] 2.7 `feedback get/list` expose `event_id`, `item_type`, `item_id`, `rating`, `note`, `attempt_id`, `created_at`, `agent_recorded`, `correctable`.（实现/文档/测试已在当前树核对）

## 3. Agent prompts and contracts

- [x] 3.1 Update `workbench/bridge/agent_contracts.py` `attempts` topic with the evaluation commands, expected-value rule, hard-delete/no-replay boundary, and Agent-chosen rating.（实现/文档/测试已在当前树核对）
- [x] 3.2 Update `workbench/bridge/conversations.py::_prompt` topic description to `attempts（记录/更正作答与评价）` and add the read-before-modify line.（实现/文档/测试已在当前树核对）
- [x] 3.3 Update `TASK_ROUTER.md` with evaluation list/get/update/delete routing.（实现/文档/测试已在当前树核对）
- [x] 3.4 Update `docs/PRODUCT-MANUAL.md` chapter 8 with the same-row edit rule and the score-ownership change.（实现/文档/测试已在当前树核对）

## 4. Tests

- [x] 4.1 Agent edits and deletes a browser-written problem evaluation.（实现/文档/测试已在当前树核对）
- [x] 4.2 Agent edits and deletes an Agent-written problem evaluation without redirecting to `attempts correct`.（实现/文档/测试已在当前树核对）
- [x] 4.3 Expected rating/note mismatch → conflict and zero writes; missing expected values → error.（实现/文档/测试已在当前树核对）
- [x] 4.4 Note-only (`rating=none`) evaluations can be edited and deleted.（实现/文档/测试已在当前树核对）
- [x] 4.5 kp and card evaluations can be edited and deleted.（实现/文档/测试已在当前树核对）
- [x] 4.6 Agent chooses a rating without a learner-supplied value.
  （契约文本断言 "You MAY choose it yourself…" + Agent 自选评分的 add/update 流程实测，
  test_feedback_crud.py）
- [x] 4.7 `add --attempt-id` refuses a duplicate and returns the existing event id.（实现/文档/测试已在当前树核对）
- [x] 4.8 Legacy `feedback <ws> --item ... --id ... --rating ...` still works.（实现/文档/测试已在当前树核对）
- [x] 4.9 Browser stale edit after an Agent edit still returns the existing conflict.
  （浏览器先写 → Agent update 改行 → 浏览器旧 expected 原位编辑被拒、零写入，
  test_feedback_crud.py::test_browser_stale_edit_after_an_agent_edit_is_refused）
- [x] 4.10 UI copy assertions use 「评价」.（实现/文档/测试已在当前树核对）

## 5. Verification

- [x] 5.1 `python -m pytest tests -q`（本会话已跑并通过：全仓 pytest 1,547 passed、compileall、openspec --specs --strict、guard extract-problems）
- [x] 5.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`（本会话已跑并通过：全仓 pytest 1,547 passed、compileall、openspec --specs --strict、guard extract-problems）
- [x] 5.3 `openspec validate --specs --strict`（本会话已跑并通过：全仓 pytest 1,547 passed、compileall、openspec --specs --strict、guard extract-problems）
- [x] 5.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`（本会话已跑并通过：全仓 pytest 1,547 passed、compileall、openspec --specs --strict、guard extract-problems）
- [x] 5.5 CLI smoke: `feedback get`, `update` with expected values, `delete`, stale conflict.（实现/文档/测试已在当前树核对）
- [x] 5.6 Grep gate for 「自评」 and prompt-contract assertion.
  （固化为 tests/workbench/test_terminology_gate.py：live docs/specs 全扫 + 契约与提示词
  「评价」断言，13 passed 组内全绿）
