# ADR 0027: Graph renderer module

## Status

Accepted.

## Context

The graph-physics module now exposes one Worker-backed runtime over one semantic core. Relation painting is still embedded in the Workbench SVG loop, which couples rendering cost and renderer choice to page code.

The renderer needs a real module seam: it should consume the existing graph runtime contract, own relation paint, and be replaceable without changing SQLite, `/graph/model`, relation semantics, or the solver. The current release must not carry SVG and WebGL as competing runtime implementations.

## Decision

Introduce `workbench/server/static/graph-renderer.js` as the single current graph-renderer implementation.

1. `GraphRenderer.attach(runtime, root)` consumes the existing graph runtime interface and owns relation drawing. Its handle accepts explicit render and resize requests, coalesces ordinary-motion requests into one frame, and parks after each draw; reduced-motion requests draw synchronously without scheduling renderer frames. The handle also exposes `destroy` for lifecycle cleanup.
2. The current implementation paints relation strokes and directed arrows with native WebGL2. DOM nodes remain authoritative for node appearance, labels, hit targets, selection, drag input, and accessibility.
3. Relation geometry is not reimplemented. The renderer privately consumes the exact `computePortSlots` and `edgePath` geometry from graph physics, preserving the existing per-node ports, lanes, relation bends, and endpoint clearance.
4. The retired SVG relation layer is hidden and its legacy path calls are reduced to inert hooks. It is not a runtime fallback. WebGL2 or shader initialization failure is explicit.
5. `graph-physics.js` composes the current renderer through its stable interface when a graph runtime is created. It does not monkey-patch `GraphPhysics.create`, retry-load optional modules, or choose between renderers at runtime.
6. Do not introduce Pixi, a bundler, WASM, or another rendering dependency.
7. Replacing the renderer later means replacing the module implementation while preserving its interface; returning to the old SVG implementation is a version rollback.
8. WebGL2 is a browser prerequisite. The graph page loads the renderer before its adapter; unavailable WebGL2 or renderer initialization failure is a readable terminal startup failure that terminates the newly created Worker and releases partial renderer resources. There is no dynamic script loader, retry, or SVG fallback.

## Backend boundary

No backend changes are required. SQLite, `/graph/model`, relation CRUD, Focus Map, authored graph data, and Agent contracts remain unchanged.

## Consequences

- Expensive relation tessellation/paint moves to the dedicated renderer module while DOM interaction semantics remain intact.
- Physics remains the source of truth for routing geometry, avoiding visual-semantic drift between solver and renderer.
- There is one current renderer path and no runtime fallback branch.
- The change is a two-way door through Git rollback and does not migrate user data.
