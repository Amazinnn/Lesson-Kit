# Handoff status

- Spec artifacts were committed and strict-validated in `8c922ac0`.
- Navigation and mount/dispose implementation were committed in `50dce8de`; disposal and stale-callback fixes with added regressions were committed in `e62cda05`.
- Graph dashboard and detail actions now belong to the swappable graph middle page; the server emits the same Agent rail on every route. Common `aiPostTurn` resets the activity rail for composer and goal-assist turns. Source and focused regressions were committed in `df26269a`.
- Focused evidence on `df26269a`: `tests/workbench/test_ui_routes.py` passed 70 tests; `node --test tests/workbench/workbench_ui_interactions.test.js` passed 129 tests; targeted OpenSpec validation, workbench compileall, JavaScript syntax check, and `git diff --check` passed.
- Independent Chromium identity, lifecycle, back/forward, dynamic-context, and graph transition acceptance is pending against `df26269a`.
- Queue and recovery work remains scoped to `complete-agent-message-lifecycle`.
