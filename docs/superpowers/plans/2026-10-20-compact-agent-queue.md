# Compact Agent Queue Implementation Plan

Goal: implement the approved d3762157 change and local browser preview using existing Soft Mondrian theme tokens.
Architecture: Shell renders and invokes thin API routes; Bridge owns order, serial provider ownership and stop handoffs; Domain/Data remain unchanged. Existing conversation/turn JSON is the sole durable message authority.
Tech stack: Python stdlib, vanilla JS, existing CSS tokens and pytest/Node checks. No new dependency or SQLite migration.

## Global constraints

- Requirements: openspec/changes/compact-agent-queue-and-direct-interrupt/{design.md,specs/*/spec.md,tasks.md}.
- The accepted preview is a behavioral/layout reference, not a new color palette. Use --lk-* / --dsw-* existing tokens, warm paper backgrounds, ink borders, restrained blue/yellow accents.
- Queue is FIFO by default, explicit server-confirmed reorder changes execution order. Only queued messages belong in queue_order and queue UI.
- Interrupt handoff is not a queue entry; waiting_for_stop persists only for stop acknowledgement/worker release. No concurrent providers, implicit queue fallback or automatic restart replay.
- Preserve submitted identity, edited text and originally captured context. Ordinary duplicate submit remains reconciliation only; send-now is an explicit separate operation.
- Pending Paper approval rejects interrupt/send-now before mutation, while explicit queue still retains work paused.
- Retained peers stay paused after interrupt; no implicit deletion. Recovery remains explicit, compact, deduplicated, and never overwrites a newer draft.
- Do not change pool schema, real course data, pipeline, pool/scripts, lessonkit.py, or unrelated UI/graph/practice behavior.
- Not alone in the repository: preserve other edits. Production code only in the isolated linked worktree; do not touch live service until acceptance and idle-session audit.

## Task 1: Bridge order and direct handoff (worker)

Files: workbench/bridge/conversations.py; workbench/server/{api.py,app.py}; tests/workbench/{test_conversations.py,test_api.py}; FILE_CONTRACT.md. Add focused Python tests in same workbench tests directory if clearer.

Interfaces consumed: existing start_turn, _dispatch_next_locked, _start_turn_locked, edit_pending/remove_pending, _LOCK, accepted message identity and Paper approval helpers.
Interfaces produced:
- GET existing session exposes queue_order (confirmed queued turn IDs only), and messages carry current queue_revision. Existing legacy data missing queue_order reads numeric-ID FIFO without bulk writes.
- POST /api/w/{name}/ai/sessions/{conversation_id}/queue/reorder with {expected_order,turn_ids}; exact permutation and expected-order CAS under ownership lock; return {conversation_id,queue_order}; invalid request 400, stale/ineligible 409, no partial mutation.
- POST /api/w/{name}/ai/sessions/{conversation_id}/turns/{turn_id}/interrupt with {expected_revision}; preserve accepted turn identity/current text/context, return canonical top-level turn response; already promoted same-target repetition returns canonical current result; changed revision or ordinary started target conflicts. Reject invalid integer bool too.
- Existing queue_action=interrupt never falls back to ordinary queue, starts directly while idle even when ordinary peers paused, binds old running worker and waits for actual release while active; rejects another handoff or pending approval before accepting a distinct submission.

Steps:
- [x] Read contracts and call sites; synchronize FILE_CONTRACT with the change before modifying behavior.
- [x] Add and run focused failing tests for order CAS, legacy order, promotion identity/idempotence and revision/dispatch races, no-queue interrupt, idle paused peers, approval rejection, stop/finish races, recovery no replay.
- [x] Minimal implementation using existing ownership and artifacts. Keep normal FIFO and manual continuation behavior.
- [x] Run covering Python suites including existing conversation and API cases; report commands/results and commit only owned files.
- [x] Write full implementation report .superpowers/sdd/backend-report.md; return status, commit and short results only.

## Task 2: Composer UI (fresh worker after backend)

Files: workbench/server/pages.py, workbench/server/static/{workbench.js,agent-ui.css,workbench.css if retiring superseded rules}; tests/workbench/{workbench_ui_interactions.test.js,agent_session_ui.test.js,test_ui_routes.py if markup assertions affected}.
Interfaces: use Task 1 API paths/payloads/canonical queue_order; all existing edit/delete/continue endpoints and event streaming stay compatible.

Steps:
- [x] Read current UI mounting, outbox/history, theme and DOM test helpers. Add and demonstrate failing checks before production code.
- [x] Put one compact queue directly above input in composer shell, rows with preview/tooltip, drag handle and keyboard reorder, send-now, edit/save/cancel, remove; four-row max height and internal scrolling. One heading/status/continue, no per-row repeated status copy. Empty queue hides panel entirely.
- [x] Distinct waiting-for-stop status outside list; filter pending list to queued only. Preserve polls while waiting for stop and active reply streaming on acceptance.
- [x] Compact recoverable outbox summary with count and expandable per-item actions, preserve existing identities, original text/context, explicit reconcile/retry, and newer draft. Failed accepted messages remain truthful in history rather than repeated giant cards.
- [x] Capture workspace/conversation/sequence/revision for mutations and async callbacks; stale conflicts refresh authoritative state, do not overwrite executing work or another conversation. Keyboard focus usable after rows refresh.
- [x] Use project CSS variables; do not copy preview dark green. Run focused JS/UI route tests, report evidence and commit owned files. Report .superpowers/sdd/frontend-report.md.

## Task 3: Contract closeout and acceptance (controller)

Files: docs/{GLOSSARY,ARCHITECTURE,PRODUCT-MANUAL,ACTION-GRAPH}.md and affected action-graph subordinate docs, change tasks/status and current specs on archive. No unimpacted DATA_MODEL rewrite.

- [x] Reconcile impacted terms, operations/levels and user manual after implementation. Correct the question-mark corrupted proposal-validation sentence in change tasks without losing its provenance.
- [x] Independent task reviews and final whole-branch review; fixes must carry covering checks. Constrained automatic acceptance unavailable because runtime cannot enforce read-only sandbox; ordinary read-only review plus controller acceptance.
- [x] Full pytest tests, compileall, strict all/spec OpenSpec and dmath extract guard; problem-set guard only if matching generated output exists.
- [x] Isolated registered pool copy and fake provider real HTTP/browser walkthrough of ordering, promotion, interrupt-only, restore, conflicts/approval, desktop+narrow theme, and unchanged practice shell. Never use real provider or real course writes for walkthrough.
- [x] Reconcile/archive only this completed change with existing OpenSpec CLI; leave unrelated active graph/ingestion changes alone. Run final OpenSpec strict and changed checks.
- [x] Integrate to main preserving preexisting dirty files.
- [ ] Push authorized delivery and check final commit CI (external deployment receipt records the result).
- [x] Update running 3081 only once idle and no stop handoff; close only its idle owned provider descendants, restart using managed daemon command from main; verify actual HTTP page and static bytes against final checkout. This feature requires no database migration.
- [x] Durable handoff with evidence and limitations; leave user's existing worktrees/data untouched.
