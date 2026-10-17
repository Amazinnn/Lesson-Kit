# Handoff status

- Spec artifacts were committed and strict-validated in `8c922ac0`.
- Navigation and mount/dispose implementation were committed in `50dce8de`; disposal and stale-callback fixes with added regressions were committed in `e62cda05`.
- Graph dashboard and detail actions now belong to the swappable graph middle page; the server emits the same Agent rail on every route. Common `aiPostTurn` resets the activity rail for composer and goal-assist turns. Source and focused regressions were committed in `df26269a`.
- Focused evidence on `df26269a`: `tests/workbench/test_ui_routes.py` passed 70 tests; `node --test tests/workbench/workbench_ui_interactions.test.js` passed 129 tests; targeted OpenSpec validation, workbench compileall, JavaScript syntax check, and `git diff --check` passed.
- Independent Chromium acceptance passed against `df26269a`: literal rail/input/messages/context/Float identities, draft/caret/scroll/activity retention, dynamic context, five middle views and back/forward; normal-to-graph node keyboard activation/detail/Open KP and direct-graph-to-practice visible chat; practice submission and graph filter remount; cancelled stale callback caused no mutation or additional pull. Only isolated fixture data was used.
- Queue and recovery work remains scoped to `complete-agent-message-lifecycle`.

- Final independent gates on source `df26269a`: official Node 216/216, compilation, strict OpenSpec 26/26 before archive (24/24 after archive), and extraction guard passed. Initial full Python was 1049 passed / 2 failed: one obsolete initial graph-dashboard assertion and one Windows temporary-directory cleanup lock. The Pi RPC case passed its isolated retry; the static assertion is corrected separately in tests. Exact-head PR CI must pass the complete Python suite before merge; no second full local run was substituted for that gate.
