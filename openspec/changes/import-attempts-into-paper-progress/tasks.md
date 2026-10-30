## 1. Data layer

- [ ] 1.1 Add `paper_progress.preview_binding(pool, paper_id, problem_ids)` returning mode, execution id, per-item positions/current states/actions, progress before/after, and completion preview; zero writes.
- [ ] 1.2 Add `paper_progress.bind_attempts(pool, paper_id, links)` for active, parked, and new checkpoints; validate Paper membership, continuation availability, generation, and content revisions before any write.
- [ ] 1.3 Build a new checkpoint with `source_kind=paper`, current generation, allocated `execution_id`, `reveal_timing=on_submit`, full ordered items, and no active-practice or `practice_runs` row.
- [ ] 1.4 Add `active_practice.bind_attempt(position, attempt_id)` that sets `answered`, links the attempt, clears a pending draft and stuck mark, preserves `reference_viewed`, and does not archive per item.
- [ ] 1.5 Add `active_practice.finish_if_complete()` that archives a legacy execution once when no item is pending and leaves explicit-mode executions for the learner's submission.
- [ ] 1.6 Add `practice_sets.append_saved(paper_id, problem_id)` with idempotent end-append, generation bump, active-item append, and checkpoint append; refuse invalid Papers and unvalidated continuations.

## 2. CLI and manifest

- [ ] 2.1 Accept optional top-level `paper_id` in the attempt manifest; validate Paper membership and current Paper availability.
- [ ] 2.2 Extend `attempts check` with a zero-write `paper` preview.
- [ ] 2.3 Extend `attempts apply` to bind after recording, persist binding fields in `attempt_operations.result`, and keep request-id replay exact.
- [ ] 2.4 Include `paper_id` in the idempotency fingerprint and reject a reused request id with different content.
- [ ] 2.5 Add read-only Paper linkage to `attempts get`.
- [ ] 2.6 Add `lesson-kit papers <workspace> append <ps-NNN> --problem <id>` and its JSON receipt.
- [ ] 2.7 Update the `attempts` help text and `surface.py` command notes.

## 3. Agent prompts and contracts

- [ ] 3.1 Update `workbench/bridge/agent_contracts.py` `attempts` topic with `paper_id`, binding modes, re-binding, completion, and the read/record boundary.
- [ ] 3.2 Update the `practice` topic with `papers append` and its difference from `papers update`.
- [ ] 3.3 Update the `content` topic with the governed missing-problem creation sequence and source-fidelity rule.
- [ ] 3.4 Update `workbench/bridge/conversations.py::_prompt` with a short Paper-import and missing-problem rule; keep ordinary tutoring zero-write.
- [ ] 3.5 Update `TASK_ROUTER.md` attempts and papers rows.

## 4. Tests

- [ ] 4.1 Cover active explicit binding, active legacy completion, parked binding, new checkpoint creation, and untouched selected Paper.
- [ ] 4.2 Cover re-binding an answered/stuck item and old attempt retention.
- [ ] 4.3 Cover ungraded import changing only execution progress.
- [ ] 4.4 Cover invalid Paper/member/batch rollback and idempotent replay.
- [ ] 4.5 Cover `attempts check` zero writes.
- [ ] 4.6 Cover append on active, parked, and no-progress Papers; idempotent repeat; invalid/duplicate refusal.
- [ ] 4.7 Cover `papers append` CLI end to end.
- [ ] 4.8 Cover the Agent contract text for `paper_id` and the three-step repair.

## 5. Contracts and docs

- [ ] 5.1 Sync the four capability deltas into `openspec/specs/` at archive time.
- [ ] 5.2 Update `FILE_CONTRACT.md` with the attempt manifest contract.
- [ ] 5.3 Update `docs/DATA_MODEL.md` with import binding, checkpoint creation, and the distinction between learning and execution progress.
- [ ] 5.4 Add `导入绑定` and `Paper 追加题` to `docs/GLOSSARY.md`; update `试卷执行进度`.
- [ ] 5.5 Update `docs/PRODUCT-MANUAL.md`, `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`.
- [ ] 5.6 Register the new actions and workflow in `docs/ACTION-GRAPH.md` and `docs/action-graph/L1-L4`.

## 6. Verification

- [ ] 6.1 `python -m pytest tests -q`
- [ ] 6.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`
- [ ] 6.3 `openspec validate --specs --strict`
- [ ] 6.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`
- [ ] 6.5 Temporary-workspace smoke: save Paper, check/apply import, read progress, append a problem, import again, submit.
