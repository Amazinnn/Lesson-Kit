# 2026-08-22 Workbench UI Information Hierarchy

## What changed

- The three-column workbench now uses a shared reading order: context, page title,
  primary content or action, then named supporting sections.
- The top bar presents workspace context; the left rail groups workspace switching,
  navigation, and weak knowledge points; the right rail separates AI identity,
  context, actions, conversation, and input.
- Practice, session-end, knowledge-point, graph, and hub pages received dedicated
  semantic sections and clearer action priority while keeping existing routes,
  DOM IDs, and learning behavior.
- Shared client logic now binds practice controls only on practice pages. A
  same-workspace temporary marker starts a new similar-practice round and renders
  `暂无更多同类题。` only when that round has no first problem.
- Canonical `workbench-ui` spec uses the current OpenSpec `## Requirements`
  heading so strict validation remains available.

## Test coverage

- Added Node standard-library interaction tests, run by pytest, for workspace
  switching, session-end rating removal, and similar-practice restart/empty state.
- Added route and SQLite fixture coverage for workspace-record persistence, wiki
  navigation, and page hierarchy landmarks.

## Verification

- `python -m pytest tests -q` — `164 passed in 35.10s`
- `node --check workbench/server/static/workbench.js`
- `openspec validate workbench-ui --strict`
- Read-only smoke on `http://127.0.0.1:3081/`: hub, practice, knowledge list,
  knowledge-point detail, graph, session end, CSS, and JS all returned 200.

Commits: `297e40b` (requirements and v4 design), `24c21f0` (implementation and tests).
