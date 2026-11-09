## 1. Data layer

- [x] 1.1 Add `paper_progress.preview_binding(pool, paper_id, problem_ids)` returning mode, execution id, per-item positions/current states/actions, progress before/after, and completion preview; zero writes.（实现/契约/测试已在当前树核对）
- [x] 1.2 Add `paper_progress.bind_attempts(pool, paper_id, links)` for active, parked, and new checkpoints; validate Paper membership, continuation availability, generation, and content revisions before any write.（实现/契约/测试已在当前树核对）
- [x] 1.3 Build a new checkpoint with `source_kind=paper`, current generation, allocated `execution_id`, `reveal_timing=on_submit`, full ordered items, and no active-practice or `practice_runs` row.（实现/契约/测试已在当前树核对）
- [x] 1.4 Add `active_practice.bind_attempt(position, attempt_id)` that sets `answered`, links the attempt, clears a pending draft and stuck mark, preserves `reference_viewed`, and does not archive per item.（实现/契约/测试已在当前树核对）
- [x] 1.5 Add `active_practice.finish_if_complete()` that archives a legacy execution once when no item is pending and leaves explicit-mode executions for the learner's submission.（实现/契约/测试已在当前树核对）
- [x] 1.6 Add `practice_sets.append_saved(paper_id, problem_id)` with idempotent end-append, generation bump, active-item append, and checkpoint append; refuse invalid Papers and unvalidated continuations.（实现/契约/测试已在当前树核对）

## 2. CLI and manifest

- [x] 2.1 Accept optional top-level `paper_id` in the attempt manifest; validate Paper membership and current Paper availability.（实现/契约/测试已在当前树核对）
- [x] 2.2 Extend `attempts check` with a zero-write `paper` preview.（实现/契约/测试已在当前树核对）
- [x] 2.3 Extend `attempts apply` to bind after recording, persist binding fields in `attempt_operations.result`, and keep request-id replay exact.（实现/契约/测试已在当前树核对）
- [x] 2.4 Include `paper_id` in the idempotency fingerprint and reject a reused request id with different content.（实现/契约/测试已在当前树核对）
- [x] 2.5 Add read-only Paper linkage to `attempts get`.（实现/契约/测试已在当前树核对）
- [x] 2.6 Add `lesson-kit papers <workspace> append <ps-NNN> --problem <id>` and its JSON receipt.（实现/契约/测试已在当前树核对）
- [x] 2.7 Update the `attempts` help text and `surface.py` command notes.（实现/契约/测试已在当前树核对）

## 3. Agent prompts and contracts

- [x] 3.1 Update `workbench/bridge/agent_contracts.py` `attempts` topic with `paper_id`, binding modes, re-binding, completion, and the read/record boundary.（实现/契约/测试已在当前树核对）
- [x] 3.2 Update the `practice` topic with `papers append` and its difference from `papers update`.（实现/契约/测试已在当前树核对）
- [x] 3.3 Update the `content` topic with the governed missing-problem creation sequence and source-fidelity rule.（实现/契约/测试已在当前树核对）
- [x] 3.4 Update `workbench/bridge/conversations.py::_prompt` with a short Paper-import and missing-problem rule; keep ordinary tutoring zero-write.（实现/契约/测试已在当前树核对）
- [x] 3.5 Update `TASK_ROUTER.md` attempts and papers rows.（实现/契约/测试已在当前树核对）

## 4. Tests

- [x] 4.1 Cover active explicit binding, active legacy completion, parked binding, new checkpoint creation, and untouched selected Paper.（实现/契约/测试已在当前树核对）
- [x] 4.2 Cover re-binding an answered/stuck item and old attempt retention.（实现/契约/测试已在当前树核对）
- [x] 4.3 Cover ungraded import changing only execution progress.（实现/契约/测试已在当前树核对）
- [x] 4.4 Cover invalid Paper/member/batch rollback and idempotent replay.+ 未知 Paper 拒绝零写入（attempt_operations 也零写）；中段写入失败（第二个条目 `_record` 注入 OSError）已验证第一批 attempt、operation 与 Paper 进度整批回滚；非成员题目拒绝与相同 manifest 幂等重放由既有用例覆盖。
- [x] 4.5 Cover `attempts check` zero writes.（实现/契约/测试已在当前树核对）
- [x] 4.6 Cover append on active, parked, and no-progress Papers; idempotent repeat; invalid/duplicate refusal.（实现/契约/测试已在当前树核对）
- [x] 4.7 Cover `papers append` CLI end to end.（实现/契约/测试已在当前树核对）
- [x] 4.8 Cover the Agent contract text for `paper_id` and the three-step repair.尝试：attempts/practice/content 三主题 + `_prompt` 的 paper_id、绑定三模式、无 rating 边界、三步补题、显式意图门槛（讨论不写入）共 4 个用例 11 passed。

## 5. Contracts and docs

- [x] 5.1 Sync the four capability deltas into `openspec/specs/` at archive time.归档为 `archive/2026-11-09-import-attempts-into-paper-progress`；live specs strict 26/26；四 capability 15 项逐块验证全过（ADDED 在场/场景保全/收窄措辞落 live）。
- [x] 5.2 Update `FILE_CONTRACT.md` with the attempt manifest contract.（实现/契约/测试已在当前树核对）
- [x] 5.3 Update `docs/DATA_MODEL.md` with import binding, checkpoint creation, and the distinction between learning and execution progress.（实现/契约/测试已在当前树核对）
- [x] 5.4 Add `导入绑定` and `Paper 追加题` to `docs/GLOSSARY.md`; update `试卷执行进度`.（实现/契约/测试已在当前树核对）
- [x] 5.5 Update `docs/PRODUCT-MANUAL.md`, `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`.（实现/契约/测试已在当前树核对）
- [x] 5.6 Register the new actions and workflow in `docs/ACTION-GRAPH.md` and `docs/action-graph/L1-L4`.（实现/契约/测试已在当前树核对）

## 6. Verification

- [x] 6.1 `python -m pytest tests -q`（本会话已跑并通过：全仓 pytest 1,547 passed；2026-11-09 收尾会话复跑 **1,613 passed / 477.25s**，compileall、openspec --specs --strict、guard extract-problems 同过）
- [x] 6.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`（2026-11-09 收尾复跑通过）
- [x] 6.3 `openspec validate --specs --strict`（2026-11-09 复跑 26/26 + `--all --strict` 42/42 通过）
- [x] 6.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`（本会话已跑并通过：全仓 pytest 1,547 passed、compileall、openspec --specs --strict、guard extract-problems）
- [x] 6.5 Temporary-workspace smoke: save Paper, check/apply import, read progress, append a problem, import again, submit.隔离临时工作区真实 CLI+浏览器六步全过（A–G），证据 `evidence.md`：check 零写入（24 表快照 diff 空）、apply 只写 attempt+绑定、浏览器恢复导入进度并继续作答后交卷归档、活动卷/停放卷互不干扰、受治理补题+append 幂等+重放零重复、三类拒绝零残留。
