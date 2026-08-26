## Why

The workbench is close to daily use, but several visible surfaces still expose implementation detail or source-data damage instead of supporting direct study. Before changing behavior, the project needs one durable decision record that separates verified causes from design choices for graph readability, learning-state presentation, problem rendering, and content ingestion.

## What Changes

- Audit the native knowledge graph against its current force model and the project's earlier discrete-mathematics visualization intent, then define a readability contract for dense relations.
- Decide which learning-state evidence remains visible, which becomes on-demand, and which stays as a background ordering mechanism.
- Define a safe boundary between supported mathematical markup and malformed OCR/HTML artifacts instead of treating all raw tags as either trusted or displayable text.
- Decompose content ingestion into independently callable operations while retaining one governed CLI and the existing pool as source of truth.
- Record additional daily-use gaps found by systematic review, without expanding this change into unrelated features.

This proposal starts a design discussion. It does not authorize production-code changes, schema changes, or modifications to existing pipeline behavior.

## Capabilities

### New Capabilities

None currently proposed.

### Modified Capabilities

- `workbench-ui`: graph readability, concise learning-state presentation, and safe problem-content rendering.
- `review-workbench`: the user-facing boundary between current state, background scheduling, and study actions.
- `knowledge-figures`: the role of course-wide and focused graph views in mathematical visualization.
- `workbench-content-governance`: composable extraction, cleaning, structuring, validation, and pool-maintenance operations.

## Impact

The design may later affect `workbench/server/`, workbench-only CLI modules, tests, and documentation. Existing `domain`, `data`, `pipeline/`, `pool/scripts/`, `lessonkit.py`, public routes, learning-write semantics, and SQLite contracts remain unchanged unless a later approved specification explicitly justifies an exception.
