# ADR 0028: Graph LOD and local layout seed ownership

## Status

Accepted.

## Context

After Worker-backed layout and a dedicated renderer module, two client-only optimizations remain useful: reducing DOM paint outside the viewport and reopening an unchanged graph near its last settled layout.

They should not create a new presentation layer. Viewport/label policy is renderer responsibility; coordinate seeds are layout-runtime responsibility. Neither belongs in SQLite or `/graph/model`.

## Decision

Keep both behaviors inside the modules that already own them.

1. `graph-renderer.js` owns viewport culling and label/meta LOD. Off-screen DOM wrappers are hidden without removing nodes from graph physics. Selected, hovered, and high-focus labels remain visible at lower zoom.
2. `graph-physics.js` owns the local settled-coordinate seed because it owns the Worker runtime and coordinate authority.
3. Store at most one layout seed per workspace in browser `localStorage`, under `lk_graph_layout_v1_<workspace>`. The stored value contains a readable, deterministic identity made from sorted node IDs and sorted `source|target|type|direction` relation tuples, plus node coordinates. This topology identity does not include edge strength, titles, metrics, or learner state. Do not introduce a graph hash or opaque cache identifier.
4. A seed is accepted only when its stored graph identity exactly matches the current graph identity.
5. Restored coordinates become temporary anchors, are sent through the existing Worker control channel, then are released and reheated. The cache never becomes authored layout truth.
6. Missing, stale, corrupt, or unavailable local storage simply means there is no seed; the same Worker implementation starts from its deterministic initial layout. This is absence of optional cached state, not a fallback implementation.
7. Do not persist filters, learner state, authored relations, graph semantics, or any backend content.
8. Do not add `graph-presentation.js`, a plugin manager, or another runtime abstraction layer.

## Backend boundary

No backend migration or API change is required. SQLite, `/graph/model`, relation CRUD, Focus Map, authored content, and Agent contracts remain unchanged.

## Consequences

- Renderer paint policy and layout-runtime state stay behind their existing module boundaries.
- Large graphs reduce DOM paint without weakening solver semantics.
- Reopening an unchanged graph preserves a useful mental map while still re-solving current constraints.
- Clearing browser storage only removes the seed and does not lose authored or learning data.
- The current version still has one renderer and one Worker-backed layout implementation; rollback remains a Git/release operation.
