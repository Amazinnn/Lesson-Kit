# Tasks

## 1. Bootstrap repair and focused regressions

- [x] 1.1 RED first: reproduce R2 with an unreadable renamed JSON whose bytes embed a pool entity id — init reports `valid=true` and creates the canonical file alongside it (disposable fixture only)
- [x] 1.2 Account for every file under the course subtree in the init scan: collect unreadable files with repository-relative path and reason (invalid UTF-8, malformed JSON) into the report
- [x] 1.3 Refuse canonical creation for implicated entities (entity id in file name or replacement-decoded bytes), report the entity blocked naming the implicating file, leave the pool row and mirror state untouched, and keep unimplicated entities bootstrapping
- [x] 1.4 GREEN: focused regressions for the three delta scenarios (implicated entity blocked, unattributable unreadable file reported without blocking, clean subtree reports nothing)
- [x] 1.5 Assess the per-entity write-failure escape in the bootstrap loop; if confirmed, capture the exception as that entity's failed result and continue, with a focused regression (one failing write never aborts later siblings); if the repair widens v1 scope, record the finding and defer
- [x] 1.6 Re-run the R1 restoration-retry regression (b66eb03) plus the focused mirror suite (21) and related suite (13); record evidence

## 2. Documentation and contract authority

- [x] 2.1 `docs/DATA_MODEL.md`: add the `content_mirror_state` / `content_mirror_log` field contract — columns, status lifecycle, writer/consumer boundaries (mirror engine writes; `check`/`status` read)
- [x] 2.2 Finish the four dirty drafts (`FILE_CONTRACT.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, `docs/PRODUCT-MANUAL.md`) without discarding existing edits, and commit them by explicit path
- [x] 2.3 `docs/ACTION-GRAPH.md`: register the mirror actions (`init`, `check`, `status`, `sync`) following existing conventions
- [x] 2.4 Update the changelog and document indexes for the mirror feature
- [x] 2.5 Sibling change `design.md`: replace the stale sentence saying bootstrap refuses when mirror state already exists with the implemented resumable skip-and-continue behavior
- [x] 2.6 Sibling change `tasks.md`: set checkboxes only where a named evidence artifact exists; leave rollout tasks 7.1–7.3 unchecked
- [x] 2.7 Verify every new design noun in the updated documents resolves in `docs/GLOSSARY.md`

## 3. Conversation-suite failure diagnosis (evidence, not assumption)

- [ ] 3.1 Create a throwaway worktree at `origin/main`; run the two failing tests (`ConversationTests.test_a_quiet_command_gets_the_tool_budget`, `ConversationTests.test_output_past_the_budget_is_not_a_timeout`) with `PYTHONUTF8=1`; keep the output as evidence
- [ ] 3.2 If they fail on main: document them as environment-owned (Windows subprocess spawn latency vs the 0.3s idle budget) in the PR body and handoff, with an explicit follow-up task on main; no code change in this PR. If they pass on main: escalate as a possible branch interaction before any merge step

## 4. Fresh independent review of the repaired HEAD

- [ ] 4.1 Dispatch spec review and quality/broad review as independent subagents (max 3 concurrent; per handoff contract) against the repaired, documented HEAD
- [ ] 4.2 Resolve any confirmed finding minimally and re-run the affected focused suites; record separate spec / quality / whole-branch verdicts

## 5. Isolated real-pool acceptance rerun on the final HEAD

- [ ] 5.1 c02 ledger-failure case: persist the pre-call full DB snapshot and requested JSON bytes before the operation, then assert DB atomicity and file normalization as two separate checks
- [ ] 5.2 c04 mirror E2E against the recorded post-legacy-upgrade baseline (`pr110-acceptance-c04-legacy-upgrade.json`)
- [ ] 5.3 Confirm zero writes to the 17 registered learner databases (read-only opens + final metadata readback) and zero writes to the external `Lesson-Kit-Content` snapshot

## 6. Full repository gates on the final HEAD

- [ ] 6.1 `python -m pytest tests -q` with `PYTHONUTF8=1`
- [ ] 6.2 All `tests/**/*.test.js` via `node --test`
- [ ] 6.3 `python -m compileall -q lessonkit.py workbench pipeline pool tests`
- [ ] 6.4 `openspec validate --all --strict --concurrency 3`
- [ ] 6.5 `python lessonkit.py guard extract-problems --course dmath --chapter ch06` (problem-set guard only if its output exists)

## 7. Merge sequence for PR110

- [ ] 7.1 Refresh the remote PR head; fast-forward push the local HEAD to `feat/canonical-content-sync` using the per-command credential override (do not modify global credentials)
- [ ] 7.2 Update the PR110 body to the final scope and evidence
- [ ] 7.3 Wait for the 3.11 / 3.12 checks, then merge with `--match-head-commit`
- [ ] 7.4 Verify CI on the actual merge commit

## 8. Post-merge wrap-up

- [ ] 8.1 Repoint the installed editable CLI to the accepted worktree and verify it from a neutral CWD
- [ ] 8.2 Update the handoff/status document with the delivered PR link, merge commit, check results, DB impact, and pending follow-ups
- [ ] 8.3 Record explicit follow-ups for a future change: sibling rollout tasks 7.1–7.3, the conversation-bridge timing fix on main, and (if deferred) the write-isolation widening assessment

Out of scope for this change (tracked in the sibling change or a follow-up): external `Lesson-Kit-Content` bootstrap and rollout samples, real-course synchronization, any learner-database write, re-removal of `problems.topic_label`, and archiving the sibling change while its rollout tasks remain open.
