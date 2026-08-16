## Why

Months of AI-assisted study failed because learning principles were never pinned
into specification documents — they lived only in conversation and vanished with
it. lesson-kit's creation side (pool: 28 KPs, 303 durable problems) is complete,
but its consumption side is nearly unused (2 problem attempts recorded). The
workbench makes the pool serve real, daily learning: weak-point-first review,
optional flexible feedback, and an AI teacher reached only through an external
agent CLI, never through a harness the workbench itself owns.

## What Changes

- Introduce a web workbench: a hub listing workspaces (each a lesson-kit
  folder), and per-workspace pages for weak knowledge points, problem pull,
  practice sessions, feedback, due reminders, and view reading.
- Add a super CLI (`wb`) sharing the same core logic as the web shell; both are
  thin front ends over one service layer.
- Add the learning-model core: weak-point ordering, problem pull engine,
  feedback→signal mapping, and forgetting-curve scheduling used only as a
  background reminder — never as a lock.
- Add an AI bridge: the workbench has no AI kernel. AI operations are tasks
  written to disk with an output contract, executed by an external agent CLI
  (cwd = workspace), and validated before their results are trusted.
- Add figure support for knowledge points (file-based, Markdown-referenced,
  viewable in web and Obsidian).
- **BREAKING**: none. Existing pipeline scripts, pool tables, and
  `lessonkit.py` keep their contracts. Pool changes are additive (two new
  tables, one new column).

## Capabilities

### New Capabilities

- `review-workbench`: workspace registry, weak-point list, problem pull,
  practice session, flexible feedback, background scheduling, session recovery.
- `ai-teacher-bridge`: provider config, task lifecycle, output-contract
  validation, the `explain` operation as the v1 AI operation.
- `knowledge-figures`: file-based figures attached to knowledge points,
  rendered through Markdown in both web and Obsidian.

### Modified Capabilities

- none

## Impact

- New Python stdlib-only service (extending the `serve-graph.py` pattern) plus
  a small Vite frontend reusing the existing editable-graph assets (KaTeX).
- Additive pool schema migration: `review_schedule`, `feedback_events`,
  `knowledge_points.figure_paths` — applied through the existing
  `pool_schema.py` `ensure_*` pattern; existing data untouched.
- New ADRs 0009–0014 record the confirmed design boundaries; `openspec/`
  config context and this change encode them as the working contract for all
  future agent collaboration.
- Engineering constraints: concise code, no defensive-programming sprawl, no
  hash values/SHA-256 anywhere (IDs are readable sequential identifiers), stdlib
  first, single process single port.
