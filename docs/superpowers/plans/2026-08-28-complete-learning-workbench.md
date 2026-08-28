# Complete Learning Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining daily-use gaps without turning experimental ideas into fake features.

**Architecture:** Keep the existing Shell -> Domain -> Data direction and use additive workbench APIs. Browser session state remains transient; goal and plan state remains workspace-local; Bridge actions are explicit-intent envelopes.

**Tech Stack:** Python stdlib, SQLite-compatible Pool, server-rendered HTML, vanilla JavaScript/CSS, `node:test`, pytest, OpenSpec.

## Global Constraints

- Do not modify `pipeline/`, `pool/scripts/` behavior, `lessonkit.py`, or external Agent CLI commands.
- Preserve existing routes, learning-write payloads, storage keys, and Chinese UI.
- No npm, framework, icon library, model SDK, or persistent browser coordinates.

### Task 1: Practice modes and rating cadence

**Files:**
- Modify: `workbench/server/pages.py`, `workbench/server/static/workbench.js`
- Test: `tests/workbench/test_ui_routes.py`, `tests/workbench/workbench_ui_interactions.test.js`

- [ ] Add failing tests asserting both content and rating mode controls are required.
- [ ] Run the focused tests and observe the missing-control failure.
- [ ] Add separate `practice-content-mode` and `practice-rating-mode` controls while preserving existing ids.
- [ ] Pass both values through session state and keep batch review reachable.
- [ ] Render valid `options_json` as accessible choices when present.
- [ ] Run focused Node and route tests.

### Task 2: Real goals and plan refresh

**Files:**
- Modify: `workbench/server/api.py`, `workbench/server/app.py`, `workbench/server/pages.py`, `workbench/server/static/workbench.js`
- Test: `tests/workbench/test_agent_planning.py`, `tests/workbench/test_ui_routes.py`, `tests/workbench/workbench_ui_interactions.test.js`

- [ ] Add failing CRUD and full-region refresh tests.
- [ ] Store goals in `.lessonkit/goals.json` with explicit writes only.
- [ ] Add additive goal routes and a minimal form.
- [ ] Replace the whole plan region after recalculation.
- [ ] Run targeted tests.

### Task 3: Explicit Agent selection action

**Files:**
- Modify: `workbench/bridge/conversations.py`, `workbench/server/api.py`, `workbench/server/static/workbench.js`, `workbench/server/context.py`
- Test: `tests/workbench/test_conversations.py`, `tests/workbench/workbench_ui_interactions.test.js`

- [ ] Add failing tests for ordinary-conversation no-op and explicit replacement.
- [ ] Parse and validate one optional action envelope from completed provider output.
- [ ] Return the action in the turn response without changing provider commands.
- [ ] Replace session selection only when the client sent practice intent.
- [ ] Run focused conversation tests.

### Task 4: Knowledge view sorting and projections

**Files:**
- Modify: `workbench/server/pages.py`, `workbench/server/static/workbench.js`, `workbench/server/static/graph-physics.js`
- Test: `tests/workbench/workbench_ui_interactions.test.js`, `tests/workbench/graph_physics.test.js`, `tests/workbench/test_ui_routes.py`

- [ ] Add failing tests for stable list sort toggles and graph projection selection.
- [ ] Add client-side list sorting with source-order default.
- [ ] Add a compact graph projection selector using existing node metrics only.
- [ ] Preserve multi-select, force layout, and zero-write behavior.
- [ ] Run focused tests.

### Task 5: Verification and archive

- [ ] Run `python -m pytest tests -q`.
- [ ] Run both Node syntax checks and browser tests.
- [ ] Run strict OpenSpec validation, `openspec doctor`, and both guards.
- [ ] Update the dated changelog with final evidence.
- [ ] Mark every task complete and archive the change.

