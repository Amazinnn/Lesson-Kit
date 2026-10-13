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

## Fixed-scale pan invalidation repair

Independent PR122 acceptance found that `graphApplyView()` repainted the viewport only when scale changed. During a native fixed-scale pan, the camera moved but the parked renderer received no invalidation, so nodes culled in the old viewport stayed hidden until a later background click. The accepted Edge fixture measured all four nodes back inside the viewport while their wrappers remained hidden; renderer draws stayed at 108 until pointer release, then rose to 109.

The shared camera-apply path now requests the existing coalesced renderer paint when the camera translates at unchanged scale. Auto-fit-in-frame suppression remains in place, the Worker does not reheat, and the normal reduced-motion path paints synchronously. The focused UI regression first failed on the original source (`relationPaints` 3, expected 4) and passed after the fix while also checking selection, settled edge geometry, no solver reheat, no extra reduced-motion frame, and idle parking.

Fresh focused checks after the repair: both modified JavaScript files pass `node --check`; the five-file graph/Worker/Workbench Node run is **130/130**. This implementation run did not replay the browser case; resumed browser and full-suite acceptance remain with the independent root reviewer.

Independent acceptance at `845f3b08`: spec, quality and whole-stack READY.
972 Python, 164 Node, 24 strict OpenSpec checks, compile and extraction guard
passed. Automated actual Edge/Worker/WebGL fixture-page evidence covers seed
restore/release/reheat, topology mismatch, corrupt/blocked storage, LOD and
selection, and the repaired fixed-scale native pointer pan. Panning restores
culled nodes before mouseup in both motion modes without solver reheat; reduced
paint is synchronous, stable idle draw counts stay constant, and auto-fit draws
its terminal result once. Raw database bytes and SQL are unchanged.
OpenSpec CLI archived `2026-10-13-graph-lod-layout-seeds`, synchronized both
authoritative graph specs, and strict all validation passed 23/23. Historical
pan blocker at `10e23872` remains recorded in acceptance evidence. Final
archive-head and actual merge CI are pending root gates; no manual visual or
real LLM acceptance is claimed.
