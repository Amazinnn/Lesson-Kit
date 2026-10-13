# ADR 0025: Graph physics module seam

## Status

Accepted.

## Context

The Workbench knowledge graph already has a deterministic, DOM-free semantic layout solver. Its rules are product-specific: prerequisite hierarchy, relation-strength distance preferences, readability hard floors, congestion recovery, deterministic multi-edge routing, and graph-view projections.

Future execution work needs freedom to move that solver off the UI thread without changing those semantics or the graph data contract. The seam must support replacement, not parallel implementations: one released version should have one authoritative semantic solver, and an older implementation should be recovered by version rollback rather than a runtime fallback.

## Decision

Separate the **public graph-physics interface** from the **semantic core implementation**.

1. Preserve the current solver byte-for-byte as `workbench/server/static/graph-physics-core.js`.
2. Keep `graph-physics.js` as the stable entry point used by callers and tests. In this PR it loads/exports the single current core implementation, so observable behavior does not change.
3. Future execution adapters may change where the core runs, including a Web Worker, while preserving the runtime interface used by the graph page (`nodes`, `edges`, `byId`, `graph`, `tick`, projection controls, visibility controls, routing helpers, and congestion inspection).
4. The core is an internal dependency, not a fallback implementation. Product runtime must not select between old and new solvers at runtime.
5. Execution changes must not reinterpret graph relations, learning state, layout scoring, readability limits, or `/graph/model` data. Those remain owned by the current Lesson Kit graph semantics.
6. Node/edge geometry produced after settling must remain compatible with the semantic core; performance work is not permission to replace the layout algorithm.

## Consequences

- The graph has a small, explicit module seam while retaining one semantic implementation.
- A later Worker adapter can replace execution without changing SQLite, `/graph/model`, Workbench callers, or the semantic core.
- Existing graph-physics tests remain the semantic regression suite; the runtime contract test verifies that the public seam exposes the core contract.
- No browser fallback is promised by this seam. If a future current implementation requires a capability, lack of that capability is an explicit runtime failure rather than a silent switch to an older implementation.
- There is no SQLite, HTTP API, OpenSpec capability, or user-visible behavior change in this decision.
