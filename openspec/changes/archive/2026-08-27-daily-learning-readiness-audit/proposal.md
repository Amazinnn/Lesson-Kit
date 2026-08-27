## Why

The workbench is close to routine study use, but all 303 formal problems currently lack solutions, practice state is not reliably restored, mobile navigation is incomplete, and the full knowledge graph remains visually tangled. The project also needs a truthful, read-only way to experiment with mastery classification without turning a provisional algorithm into durable student state.

## What Changes

- Add composable `wb ingest` operations and zero-write recipes with explicit Agent preparation/execution, independent source audit, deterministic content gates, and transactional apply.
- Backfill solutions for the current 303 formal problems only after every problem passes independent audit and deterministic validation; switch the pool in one recoverable transaction.
- Remove raw signal, scheduler, and manual mastery controls from student pages; show concise action reminders while retaining complete evidence for ordering, CLI, and Agent context.
- Restore practice sessions from the existing tab-scoped storage, add a knowledge-point practice handoff, surface errors inline, and provide usable mobile navigation and Agent drawers.
- Lay out graph connected components independently, select among deterministic starts by crossings/collisions/waste, pack components, curve residual close edges, and visually focus one- and two-hop neighborhoods.
- Add a read-only, versioned `mastery v0` experiment that returns explainable categories without database writes or UI authority.

## Capabilities

### New Capabilities

- `mastery-evaluation`: Read-only, explainable experimental classification of problem and knowledge-point learning evidence.

### Modified Capabilities

- `workbench-content-governance`: Composable ingestion, explicit Agent artifacts, independent audit, deterministic gates, zero-write recipes, and atomic formal-pool apply.
- `workbench-ui`: Concise study state, recoverable practice, mobile drawers, visible failures, accessible cards, knowledge-point practice entry, and focused readable graphs.
- `review-workbench`: Practice recovery semantics, action-oriented reminders, formal-problem solution completeness, and the read-only experiment boundary.
- `knowledge-figures`: Safe limited mathematical markup and component-aware graph visualization behavior.

## Impact

Implementation is limited to `workbench/`, tests, OpenSpec, documentation, a tracked solution/audit artifact, and a transactional update of the registered local SQLite pool. Existing routes, JSON learning APIs, provider compatibility, storage-key meanings, learning-write semantics, `pipeline/`, `pool/scripts/`, and `lessonkit.py` behavior remain compatible. No npm package, framework, model SDK, graph library, OCR engine, plugin framework, or mastery UI is introduced.
