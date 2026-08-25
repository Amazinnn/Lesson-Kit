# Change: Agent-native workbench conversation and governed content data plane

## Why

The right AI column is still a pair of task shortcuts rather than a real conversation, and an external Agent has no stable, documented way to inspect or intentionally maintain the knowledge pool. This makes the visible teacher surface appear connected while preventing provider-native continuity, authoritative page context, and auditable content edits.

## What Changes

- Add a unified JSON `wb data` interface for reading and deliberately changing knowledge points, formal problems, candidates, relations, and current learning state.
- Allocate new content with course/chapter-scoped readable sequence IDs and enforce candidate gate promotion as the only creation path for formal problems.
- Add transactional physical deletion with explicit cascades and no deletion log.
- Auto-discover local Codex and Claude CLIs and run provider-locked, resumable conversations using their native session stores.
- Mirror only successful explicit question/answer exchanges, provider session IDs, context anchors, and change summaries under `.lessonkit/jobs/conv-###/`.
- Replace visible explain/diagnose shortcuts with free conversation, session selection, provider selection, cancellation, optional daily creation, and server-rebuilt page context.
- Add a dedicated `workbench-content-governance` capability.

## Capabilities

- `ai-teacher-bridge`
- `workbench-ui`
- `review-workbench`
- `workbench-content-governance` (new)

## Impact

New workbench Data/Bridge/Shell modules, additive `content_sequences` migration through `pool_schema.py`, internal HTTP routes, right-column markup/JS/CSS, and tests. Existing routes, explain/diagnose APIs and CLI, pipeline scripts, `lessonkit.py`, provider authentication, and learning-write bodies remain compatible.
