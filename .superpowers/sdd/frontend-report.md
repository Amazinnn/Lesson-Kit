# Task 2 frontend report: compact agent queue

Frontend implementation is committed as `409712ad` (`feat: compact agent queue composer UI`). The commit contains only the six assigned UI and test files. Controller-owned `tasks.md` and `docs/STATUS-compact-agent-queue-2026-10-20.md` remain outside the commit.

## Behavior delivered

- The queue now sits directly above the composer. It shows queued turns only, follows the server-confirmed order, caps the list at four 46px rows before internal scrolling, and provides preview tooltips, pointer drag, keyboard reorder, send-now, edit/save/cancel, and remove actions.
- `waiting_for_stop` is rendered as a separate short status. It never appears in the queued list, and its 350ms status poll continues while the active stream remains intact.
- Unchanged queue rows retain their DOM across polls. The render key includes workspace, conversation, sequence, queued IDs/order/content/revisions, approval state, and edit state. Editing retains the learner's draft and focus; save sends the revision captured when editing began, so an intervening change conflicts instead of overwriting it.
- Unknown and rejected sends appear in one counted, expandable recovery summary. Accepted failures stay in conversation history with their error and a linked inline retry. Reconciling an unknown send reuses its original submission identity; retrying an accepted failure uses a fresh identity, preserves saved route/selection context, and follows the current send preference. Restoring rejected text leaves a newer composer draft untouched.
- Queue, recovery, and responsive composer styles use the existing Soft Mondrian `--lk-*` / `--dsw-*` tokens.

## Red/green and verification evidence

Before the production edits, the new queue behavior checks failed on the absent waiting status, queue controls/order, row editing, and recovery summary; the route assertion failed because the separate handoff status was absent from the page. The focused Node and route suites passed after implementation.

Final focused results:

- `node --test tests/workbench/agent_session_ui.test.js` — **43 passed**.
- `node --test tests/workbench/workbench_ui_interactions.test.js` — **124 passed**.
- `PYTHONUTF8=1 python -m pytest tests/workbench/test_ui_routes.py -q` — **70 passed**.
- `node --check workbench/server/static/workbench.js` — passed.
- `git diff --check` and staged whitespace check — passed.

The new tests cover queued-only filtering and continued waiting polls, same-row DOM identity and keyboard focus across a poll, confirmed reorder and send-now revision payload, edit draft/focus preservation with the original revision, compact/deduplicated recovery, truthful inline failure, and context-preserving retry.

## Browser handoff evidence

The controller reported isolated-fixture browser checks at desktop and narrow widths: six queued rows remain behind a 184px internal scroller with the composer visible; at 390px, controls wrap without horizontal overflow. After stable-row reuse, ordinary edit click succeeded, the draft and focus survived a 900ms poll, and save used the captured revision. The keyboard handle retained focus after an 850ms poll; ArrowUp produced the server-confirmed C/B/D order. HTML5 drag reorder, removing D, and send-now on C also succeeded; C kept its existing turn identity, A was cancelled, B remained paused, and the newer composer draft stayed intact. In a separate interrupt scenario, the handoff stayed outside the queue, A cancelled, D completed, and a later ordinary E completed without the retained backlog blocking it. The browser used the isolated fake-provider fixture and read-only course copy.

The controller owns repository-wide verification and rollout. It reported one full-suite failure from the controller-owned surface route inventory, fixed separately in `765fb909`, with its covering route check at **5 passed**. A subsequent full Node run reported **245 passed**; the second repository-wide pytest run was still in progress at 64% with no failures observed at that point. No live-service change, course-data write, API/backend edit, or controller documentation change is included in this frontend commit.
