# ADR 0025: Graph physics execution boundary

## Status

Accepted.

## Context

The Workbench knowledge graph already owns a deterministic, DOM-free semantic layout solver in `workbench/server/static/graph-physics.js`. Its layout rules are product-specific: prerequisite hierarchy, relation-strength distance preferences, readability hard floors, congestion recovery, deterministic multi-edge routing, and graph-view projections.

The current browser page also executes that solver on the main thread. Future renderer and scheduling work needs freedom to move physics off the UI thread without changing those semantics or the graph data contract.

## Decision

Separate **semantic physics** from its **execution adapter**.

1. Preserve the current solver byte-for-byte as `workbench/server/static/graph-physics-local.js`.
2. Keep `graph-physics.js` as the public compatibility entry point. In this first step it remains byte-identical to the local solver, so observable behavior does not change.
3. New execution adapters may delegate the solver to another execution context, including a Web Worker, but must preserve the existing public runtime contract used by the graph page (`nodes`, `edges`, `byId`, `graph`, `tick`, projection controls, visibility controls, routing helpers, and congestion inspection).
4. Execution adapters must not reinterpret graph relations, learning state, layout scoring, readability limits, or `/graph/model` data. Those remain owned by the existing Lesson Kit graph semantics.
5. Node/edge geometry produced after settling must remain compatible with the local solver; performance work is not permission to replace the semantic layout algorithm.

## Consequences

- PRs can change where physics runs without coupling that change to renderer or data-model work.
- `graph-physics-local.js` is the reference implementation for parity tests.
- Existing graph-physics tests remain the semantic regression suite; a dedicated runtime-parity test compares the public entry point with the local reference.
- There is no SQLite, HTTP API, OpenSpec capability, or user-visible behavior change in this decision.
- A Worker adapter may be introduced independently and must retain a local fallback for unsupported environments and Node-based tests.
