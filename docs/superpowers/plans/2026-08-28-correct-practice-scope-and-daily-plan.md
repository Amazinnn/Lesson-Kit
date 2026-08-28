# Correct Practice Scope and Daily Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Make knowledge-view selection the only source of practice scope, enforce one explicit practice mode per session, and replace the current fabricated daily-plan output with real coarse goals and queue data.

**Architecture:** Keep Shell → Domain → Data one-way. Add planning persistence and selection orchestration only under `workbench/`; preserve existing learning-write APIs and conversation bridge. The browser stores the transient selected knowledge-point scope in existing `sessionStorage`; SQLite stores only explicit goals and the current valid plan.

**Tech Stack:** Python stdlib, SQLite, server-rendered HTML, vanilla JavaScript/CSS, `node:test` and pytest.

## Global Constraints

- Do not modify `domain` outside the planned workbench Domain modules, `pipeline/`, `pool/scripts/`, `lessonkit.py`, external Agent CLI behavior, or public learning-write request shapes.
- Knowledge-view selection is explicit; direct `/practice` with no selection shows an empty handoff state and never auto-pulls weak items.
- Agent may replace selection only after explicit practice intent; ordinary conversation must not change it.
- A practice session has exactly one mode: `exam`, `flash_card`, or `yes_no`; no silent fallback or mixed modes.
- Existing unmarked problems remain available to `exam`; Flash Card and Yes/No require explicit content metadata and may remain visibly unconfigured.
- Long-term and stage goals are independent macro cards showing title, progress, and deadline by default; details are on demand. Today’s plan is separate and coarse.
- No selection, navigation, drafting, skipping, or plan viewing writes learning records.

### Task 1: Specs and requirements correction

Update `docs/REQUIREMENTS.md`, `docs/frontend-optimization-plan.md`, `docs/FUTURE-DEVELOPMENT-NOTES.md`, and create an OpenSpec change `correct-practice-scope-and-daily-plan` with proposal, design, delta specs, and tasks. Supersede the archived daily-learning-plan claims that expose per-item mode links or invent a default course goal. Validate strictly and commit/push docs only.

### Task 2: Planning data and deterministic baseline

Add workbench-owned goal/current-plan persistence through the approved incremental SQLite schema path, with read/write Data methods and a pure Domain planner. Real goals only; no fabricated course goal, no 45-minute fiction, maximum three coarse queue items, due-only output when no goals exist, and progress as explicit formal-problem coverage rather than mastery. Add CLI/API tests for persistence, ordering, no-goal behavior, and refresh consistency. Commit/push implementation.

### Task 3: Knowledge view selection and practice handoff

Add shared explicit selection state to knowledge list and graph views. Provide one `practice-selected` handoff action carrying selected `kp_ids` to the practice start card. Remove per-KP exam/card/judgment links and the weak-list auto-selection path. Practice startup requires both a non-empty scope and one mode; `/pull` receives the selected scope, selected mode, and `exclude_ids`. Keep existing rating/session storage semantics. Add Node/Python tests for selection, no-scope empty state, single-mode filtering, no fallback, and deduplication. Commit/push implementation.

### Task 4: Goal cards and plan presentation

Render separate long-term and stage goal cards (all real goals; title, coverage progress, deadline; description/scope disclosure) plus a separate one-card daily queue with at most three holistic items. A queue handoff explicitly seeds the same selection state before showing the mode picker. Recalculate only the deterministic plan and refresh the whole plan region; do not accept arbitrary browser adjustment JSON. Add route and DOM tests. Commit/push implementation.

### Final verification

Run `python -m pytest tests -q`, targeted Node tests, `node --check workbench/server/static/workbench.js`, strict OpenSpec validation, `openspec doctor`, and both pool guards. Confirm `main == origin/main`; leave `.lessonkit/plan.json` and both `_claude_*.txt` files untracked.
