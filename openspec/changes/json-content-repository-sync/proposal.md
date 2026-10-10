# Proposal: JSON content repository sync

## Why

Real Lesson Kit course workspaces are production workspaces, not clean content trees. The audited `c02` and `c04` examples mix the knowledge pool with ingest batches, Agent jobs, figures, intermediate/QC output, repair scripts, backups, generated practice material, logs, and machine-local paths. Mirroring those folders into Git would version transient implementation debris and make course location part of the content contract.

At the same time, governed content needs a form that a web Agent can edit precisely, review through Git, and transfer to local Lesson Kit without copying SQLite databases. Existing `lesson-kit data` and Check-pipeline paths already own content validation and writes; a new path must coordinate them rather than introduce a second database writer.

## What changes

- Add a separate checked-out JSON content repository whose `courses/<course-id>/` directories contain normalized authored content, independent of where workspaces live on disk.
- Store one content entity per UTF-8 JSON file. Identity is the entity id, never the file path.
- Add a monotonically increasing integer `revision` to each mirrored entity. No content hashes, fingerprints, SHA values, or content-derived ids are introduced.
- Add `lesson-kit mirror` commands to bootstrap, check, plan, and synchronize a registered workspace against one course directory in a checked-out content repository.
- Keep the knowledge pool as the runtime source of truth. The JSON files are an equally editable projection of governed authored fields: an accepted repository edit becomes a normal validated pool mutation; an authored-field change already present in the pool can be exported as the next JSON revision.
- Keep learner/runtime state pool-only. Attempts, progress, feedback, schedules, signals, caches, sessions, statistics, and other runtime rows are never exported.
- Synchronize one entity at a time. A multi-entity run may partially succeed; each successful entity is all-or-nothing and resumable independently.
- Treat a missing JSON file as missing transport state, never as a delete instruction. Explicit deletion-request JSON may be carried and reported, but the mirror path has no physical-delete operation.
- Detect two-sided divergence and refuse silent overwrite. Normal operation is kept version-aligned so this remains exceptional.
- Reuse existing field validation/mutation authorities (`workbench.data.content`, relation policy, specialized ingest contracts) rather than direct ad-hoc SQL.

## Initial supported projection

The first implementation covers the three content entities already exposed through the governed data interface:

- knowledge points (`kp`),
- durable problems (`problem`),
- knowledge relations (`relation`).

V1 is limited to knowledge points, durable problems, and knowledge relations. It does not mirror flash-card entities, figure bytes, or specialized problem-difficulty fields, and it refuses repository-only entity creation. Expanding that boundary requires a separate approved change that names the existing validation and mutation authority for each new entity or field.

## Non-goals

- Syncing `pool/*.db` or any SQLite file.
- Mirroring an entire workspace directory.
- Replacing Git itself: clone/pull/commit/push remain ordinary Git operations; Lesson Kit operates on a local checkout.
- Inventing a second content validator or bypassing the Check/data mutation contracts.
- Automatic merge of concurrent semantic edits.
- Physical deletion from a Git-side request.
- Hash-based change detection.

## Impact

- `workbench/data/`: JSON projection, revision state, per-entity synchronization.
- `workbench/cli/main.py`: `mirror` command group.
- `pool/scripts/pool_schema.py`: additive idempotent synchronization-state tables.
- `tests/workbench/`: valid/invalid envelope fixtures, bootstrap/sync/conflict/retry/deletion tests.
- `FILE_CONTRACT.md`: canonical JSON repository envelope and directory contract.
- `docs/adr/`: architecture decision separating runtime pool from Git-backed authored projection.
- `docs/PRODUCT-MANUAL.md`, `docs/ACTION-GRAPH.md`, `docs/ARCHITECTURE.md`: user and architecture documentation on delivery.
