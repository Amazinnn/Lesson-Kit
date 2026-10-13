# Graph LOD and local layout seeds

PR122 keeps viewport culling and label/meta LOD in the existing renderer and stores at most one optional settled layout seed per workspace in browser storage. A seed is a readable, exact node-and-relation topology match used only as temporary input to the existing Worker; it does not restore filters, selection, authored data, or learning state. Cache loss or unavailable storage returns to deterministic Worker initialization.

The source integration preserves PR121's explicit core/renderer/adapter loading, terminal Worker cleanup, coalesced renderer invalidation, idle parking, and synchronous reduced-motion paint. No SQLite field, backend API, CLI, new user action, or FILE_CONTRACT change was introduced.

## Integration record

- PR122 source head before integration: `f20aaefb26cc9a3e8907e3f6c34d8fe2108c1a8f`.
- Accepted PR121 runtime/source head: `949fc81e85f631e770fef60cb239376cac5a9e97`.
- PR122/PR121 merge base: `9fde12025c3dd07e5562ead7f66fae2869ea823b`.
- Explicit source merge commit: `5a694e7f`; parent order is PR122 first, accepted PR121 second.
- Current-main integration head: `6a045650edb4b95b785c40a68320952aea3bb6f7`.
- Local main-integration merge commit: `4958c623`.

## Focused verification

- `node --check workbench/server/static/graph-physics.js` — passed.
- `node --check workbench/server/static/graph-renderer.js` — passed.
- `node --test tests/workbench/graph_layout_seed.test.js tests/workbench/graph_renderer.test.js tests/workbench/graph_physics_worker.test.js tests/workbench/graph_physics_runtime.test.js tests/workbench/workbench_ui_interactions.test.js` — **130 passed, 0 failed**.
- Independent full-suite, browser, archive, and release acceptance remains with the root integration owner.
