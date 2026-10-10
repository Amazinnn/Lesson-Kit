# ADR 0024 — Git JSON is an authored-content projection, not a runtime store

**Status:** accepted

## Context

Real course workspaces contain far more than durable authored content: the knowledge pool, ingest batches, Agent jobs, figures, intermediate/QC products, repair scripts, backups, generated outputs, logs, and machine-local paths. Mirroring a workspace folder into Git would make transient production layout part of the content contract.

The owner also needs web Agents to edit exact course-content fields through a private Git repository and have local Lesson Kit accept those edits safely. SQLite binaries are unsuitable for that workflow, while the existing knowledge pool must remain the one runtime data source used by the workbench.

## Decision

1. The course knowledge pool remains the runtime source of truth.
2. A separate Git repository may hold a normalized JSON projection of governed authored content. It has equal **editing authority for that projection**: accepted JSON edits become validated pool mutations, and authored-field pool edits can be exported back.
3. Runtime/learner state is never mirrored: attempts, progress, feedback, schedules, learner signals, sessions, caches, derived statistics, and similar state stay in the pool/workspace.
4. One repository holds many courses under Course Identifier directories. Local workspace paths are not part of the repository contract.
5. One logical entity is one JSON file. Stable entity id is identity; path is presentation.
6. Synchronization is per entity. Multi-entity runs may partially succeed, while one entity mutation is atomic and independently resumable.
7. Consistency uses monotonically increasing integer revisions plus the last synchronized normalized JSON content. No hash values, fingerprints, SHA values, or content-derived ids are introduced.
8. Git-side absence never means deletion. Explicit deletion-request files may record intent, but this synchronization path cannot physically delete pool content.
9. Lesson Kit operates on a local checkout only. Git clone/pull/commit/push and authentication remain ordinary Git concerns, outside content semantics.
10. Existing governed content validators and mutation paths remain authoritative; the synchronization layer coordinates them rather than introducing a generic SQL writer.

## Consequences

- A messy workspace and a clean workspace can produce the same repository contract.
- Git history becomes useful for field-level review without carrying runtime state.
- Bidirectional authoring is possible without contradicting the pool's runtime authority.
- Initial ancestry must be established explicitly (pool-first bootstrap); the system does not guess a winner between independently populated copies.
- Specialized authored fields are added to the projection only when their existing validation/apply contract is delegated to, so editability expands without bypassing invariants.

## Specification

`openspec/changes/json-content-repository-sync/`
