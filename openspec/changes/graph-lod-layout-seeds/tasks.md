## 1. Runtime integration

- [x] 1.1 Resolve the PR122 source conflicts against the accepted PR121 runtime while preserving explicit core/renderer/adapter loading, terminal Worker cleanup, renderer invalidation/idle parking, and reduced-motion synchronous paint.
- [x] 1.2 Retain renderer-owned viewport culling and selected/hovered/high-focus label LOD.
- [x] 1.3 Retain the readable per-workspace settled layout seed, exact topology identity, temporary Worker anchors, and deterministic cache-miss startup.

## 2. Contract reconciliation

- [x] 2.1 Add the `graph-lod-layout-seeds` change and preserve all current scenarios in the modified `workbench-ui` and `knowledge-figures` requirements.
- [x] 2.2 Define the local layout seed in the glossary and document the browser envelope and its sole reader/writer in DATA_MODEL.
- [x] 2.3 Reconcile architecture, product manual, Action Graph, ADR 0028, and changelog without changing SQLite or FILE_CONTRACT.

## 3. Focused verification

- [x] 3.1 Run the existing graph seed, renderer, Worker, runtime, and Workbench interaction Node checks.
- [ ] 3.2 Independent full-suite, browser, and release/archive acceptance remains with the root integration owner.
