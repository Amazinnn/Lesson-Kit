## Context

See `proposal.md` for motivation and the delta specs for user-visible behavior. The graph runtime is split across the physics core, Worker adapter, Worker, renderer, and the existing Workbench paint signals. PR121 makes the page load core, renderer, and adapter explicitly; its accepted renderer coalesces ordinary paint requests and parks after a draw, while reduced-motion paint is synchronous.

## Goals / Non-Goals

**Goals:**

- Preserve the accepted PR121 startup failure, Worker termination, partial-resource cleanup, coalesced invalidation, idle parking, and reduced-motion behavior while retaining PR122 LOD and cache behavior.
- Keep each concern in its current owner: viewport and label paint policy in `graph-renderer.js`; seed read/write and temporary coordinate anchors in `graph-physics.js`.
- Describe the browser cache precisely without making it a pool field, authored layout, or learner fact.

**Non-Goals:**

- Changing graph membership, relation structure, worker physics, projection rules, selection, backend APIs, SQLite, or Agent/CLI contracts.
- Adding a renderer abstraction, a cache migration, retries, or a new user action.

## Decisions

1. **Apply LOD during requested paints.** The renderer computes its viewport from the existing stage transform, hides off-screen DOM wrappers, and reduces label/meta detail by zoom. Every requested graph paint refreshes this policy, so parked renderers do not need a second loop. Selection and graph data stay in the Workbench model. An always-running frame loop was rejected because PR121 acceptance requires settled and reduced-motion rendering to park.

2. **Keep the seed in the Worker adapter.** The versioned key is `lk_graph_layout_v1_<workspace>` (using `default` when no workspace label exists). Its JSON envelope holds numeric version `1`, readable identity, and node positions. The identity is JSON over sorted node ID strings and sorted `source|target|type|direction` relation tuples. It intentionally does not assert equality of relation strength, titles, metrics, or learner state.

3. **Write only after settlement and read only on exact identity.** The adapter saves finite coordinates rounded to one decimal place on the first settled Worker snapshot in each settled period. A reheat allows one later settled write. On creation, an exact identity match supplies temporary anchors through the normal Worker control message; after two animation-frame callbacks the anchors are released and the same Worker reheats. Stale, malformed, or unavailable storage yields no seed and leaves deterministic Worker initialization in place.

4. **Keep failure handling shared with PR121.** Worker creation, message posting, renderer attachment, and Worker errors use the existing terminal `stop` path. It prevents later posts, terminates the Worker, and destroys any attached renderer. Seed storage errors are optional-cache misses and do not fail graph startup.

5. **Treat culling as paint policy.** LOD changes only DOM visibility and label/meta visibility. It does not remove nodes or relations from the model or alter selection. On-screen selected, hovered, and high-focus labels keep their low-zoom priority.

## Risks / Trade-offs

- [Risk] A graph can retain the same node/relation identity while its edge strengths, titles, or metrics change, so a seed may not reflect the best initial view for those updates → the cache is only a temporary starting point; the same Worker resumes current constraints after anchors are released.
- [Risk] Browser storage can be blocked, evicted, or cleared → the adapter treats this as a cache miss and uses normal deterministic Worker startup; clearing it does not affect authored or learning data.
- [Risk] Viewport estimates can hide content close to the edge → the renderer includes a margin and recalculates on the existing viewport and graph paint signals; culling never changes graph membership.

## Migration Plan

No database or API migration is needed. Version 1 uses one workspace-scoped browser key; an incompatible or absent value is ignored. Clearing `lk_graph_layout_v1_<workspace>` removes only the optional starting layout. Rollback is a source release rollback and may leave an ignored browser key.
