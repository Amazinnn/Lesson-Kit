## Why

The backend v1 (archived review-workbench-v1) exposes the full learning loop as
JSON APIs, but the consumption surface is still two stub pages. The learner
needs a minimal usable browser workbench: practice, knowledge display, and an
AI teacher column — nothing more. Every extra feature is rejected by design.

## What Changes

- Introduce a three-column web shell: left selector column (workspace
  dropdown + navigation), middle page area, right AI conversation column
  (collapsible).
- Practice page: pull problems from weak points, answer, reveal solutions per
  problem, optional feedback box that appears with the reveal, session-end
  unified self-rating with a single "practice similar" entry.
- Knowledge point display page: rendered body (LaTeX, wiki links, figures),
  linked problems, signals with cascade reasons.
- AI column: current/recent problems shown as priority context (display only —
  the agent sees everything through the CLI data interface and can search
  freely); explain/diagnose one-click with the current problem and answer
  text; job polling and result rendering; new sessions anytime; graceful
  message when no provider is configured (record-only when disconnected).
- Minimal `/static/` asset serving reusing the editable-graph dist KaTeX
  assets; zero build step.

## Capabilities

### New Capabilities

- `workbench-ui`: three-column shell, practice page, session-end unified
  self-rating, AI column with priority-context display, knowledge point
  display page.

### Modified Capabilities

- none

## Impact

- New HTML/JS under `workbench/server/pages.py` (server-rendered pages) plus
  small static JS/CSS served from `/static/` (KaTeX from
  `frontend/editable-graph/dist`).
- One additive API endpoint for the session-end summary if the existing
  endpoints cannot compose it (tested; archived contracts untouched).
- Explicitly deferred: review page, memory cards, agent organization panel,
  batch reveal, any extended summary, generate bridge op, Scoropic mode.
- Design note: the "one long conversation with the AI teacher" ideal is served
  by the pool as the durable record — learning records are never bound to a
  session.
