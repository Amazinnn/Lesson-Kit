# Daily Learning Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the workbench open with a stable, coarse-grained daily learning queue derived from course goals, with optional Agent adjustments and live status feedback.

**Architecture:** Keep SQLite and existing learning records as the source of truth. Add a small planning domain module that computes a deterministic baseline from goals, coverage, progress, and available problem types; expose it through existing workbench routes. The Agent can request bounded plan adjustments through the existing conversation bridge, while the UI renders only the resulting plan and a concise running status.

**Tech Stack:** Python standard library, existing SQLite data layer, existing server-rendered pages, vanilla JavaScript/CSS, node:test and pytest.

## Global Constraints

- Preserve Shell→Domain→Data one-way dependency; new code belongs in `workbench/`.
- Do not modify `pipeline/`, `pool/scripts/`, `lessonkit.py`, external Agent CLIs, or existing learning-write semantics.
- Keep current routes, workspace isolation, storage keys, and Chinese UI conventions.
- Calendar view, fitted workload curve, selectable learning models, plugin ecosystem, and AI-generated content remain experimental. This plan only adds entry selection for the already discussed exam, Flash Card, and Yes/No practice paths.
- Student-facing UI shows the final plan only; it does not expose whether baseline code or Agent adjustments produced it.

---

### Task 1: Document the planning contract

**Files:**
- Modify: `docs/REQUIREMENTS.md`
- Modify: `docs/frontend-optimization-plan.md`
- Modify: `docs/FUTURE-DEVELOPMENT-NOTES.md`
- Create: `openspec/changes/daily-learning-plan/`

**Interfaces:**
- Produces the approved vocabulary for goals, coarse daily queue, baseline planning, Agent adjustment, and status events.

- [ ] Write failing OpenSpec/requirements checks for the new contract: daily queue is coarse-grained, baseline works without Agent, Agent changes are optional, and no new state names are invented.
- [ ] Run `openspec validate daily-learning-plan --strict` and observe the expected failure before the change files are complete.
- [ ] Add proposal, design, delta specs, and tasks; quote the existing state-machine names instead of introducing new status values.
- [ ] Add the confirmed user wording before each structured summary in the future-notes section.
- [ ] Run `openspec validate daily-learning-plan --strict` and `openspec doctor`.
- [ ] Commit and push: `docs: define daily learning plan contract`.

### Task 2: Add deterministic baseline planning

**Files:**
- Create: `workbench/domain/planning.py`
- Modify: `workbench/data/queries.py`
- Modify: `workbench/server/api.py`
- Test: `tests/workbench/test_planning.py`

**Interfaces:**
- `build_baseline_plan(workspace, *, now, available_minutes=None) -> dict` returns `{goals, queue, totals, generated_at}`.
- `queue` contains coarse goal-level items with stable `id`, readable `title`, `kp_ids`, `target_count`, `difficulty_mix`, and `reason`.
- Missing numeric values use type-appropriate defaults; no new learning-state names are introduced.

- [ ] Write tests for course-order stability, deadline weighting, coverage weighting, mixed problem-type counts, missing-value handling, and repeatable output.
- [ ] Run `python -m pytest tests/workbench/test_planning.py -q` and confirm failure.
- [ ] Implement only pure planning calculations in `planning.py`; obtain facts through existing query functions and keep writes out of the baseline path.
- [ ] Add a read endpoint or route handler that returns the baseline plan for the active workspace without requiring an Agent.
- [ ] Run the target tests and confirm they pass.
- [ ] Commit and push: `feat(workbench): add deterministic daily planning baseline`.

### Task 3: Render the daily plan in the practice view

**Files:**
- Modify: `workbench/server/pages.py`
- Modify: `workbench/server/static/workbench.css`
- Modify: `workbench/server/static/workbench.js`
- Test: `tests/workbench/test_ui_routes.py`
- Test: `tests/workbench/workbench_ui_interactions.test.js`

**Interfaces:**
- Practice page renders a plan section, one coarse queue card per item, and the existing practice entry point.
- Existing DOM hooks and session semantics remain intact.

- [ ] Add failing route and Node tests asserting goal cards, today queue cards, readable knowledge-point titles, no micro-action checklist, and an empty/error state.
- [ ] Run the focused tests and confirm failure.
- [ ] Add semantic server-rendered sections with one primary action; keep explanatory copy short.
- [ ] Add minimal responsive styles and client refresh behavior without introducing a new frontend framework or build step.
- [ ] Run focused tests and `node --check workbench/server/static/workbench.js`.
- [ ] Commit and push: `feat(workbench): show daily plan on practice page`.

### Task 4: Add Agent adjustment and live status events

**Files:**
- Modify: `workbench/bridge/` existing conversation integration module
- Modify: `workbench/server/api.py`
- Modify: `workbench/server/static/workbench.js`
- Modify: `workbench/server/static/workbench.css`
- Test: `tests/workbench/agent_planning.test.js`
- Test: `tests/workbench/test_agent_planning.py`

**Interfaces:**
- Agent receives the baseline plan plus explicit student context and may return a bounded adjustment result.
- Status events use existing conversation event plumbing; UI labels are friendly text such as “正在重新安排学习计划”, “已更新今日计划”, “等待输入”.
- `POST /api/w/{workspace}/plan/recalculate` triggers an explicit recalculation; daily-first-open triggering is guarded by existing browser session/date semantics and does not run while the app is closed.

- [ ] Add failing tests for explicit recalculation, first-open-per-day behavior, queued user message while a batch runs, immediate stop, status rendering, and fallback to baseline on Agent failure.
- [ ] Run focused tests and confirm failure.
- [ ] Implement a single atomic planning batch: baseline first, optional Agent adjustment second, then one plan refresh; do not persist internal tool events as learning logs.
- [ ] Keep the stop control in the Agent header beside the back control; do not add duplicate controls elsewhere.
- [ ] Merge partial Agent output into one message/status stream and refresh affected plan cards after a completed batch.
- [ ] Run focused tests, `node --check`, and `python -m pytest tests -q`.
- [ ] Commit and push: `feat(workbench): let agent adjust daily learning plans`.

### Task 5: Final verification and handoff

**Files:**
- Modify: `changelog/2026-08-28-daily-learning-plan.md`
- Modify: `openspec/changes/daily-learning-plan/` (archive after acceptance)

- [ ] Run `python -m pytest tests -q`.
- [ ] Run `node --check workbench/server/static/workbench.js`.
- [ ] Run strict OpenSpec validation and `openspec doctor`.
- [ ] Smoke test `:3081` at desktop and narrow widths: baseline plan, Agent status, stop, fallback, and refresh behavior.
- [ ] Record only final behavior and verification evidence in the changelog.
- [ ] Archive the OpenSpec change, commit, push, and confirm `main == origin/main`; leave both `_claude_*.txt` files untouched.
