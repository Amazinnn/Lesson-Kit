## Why

PR121 introduces a single WebGL2 path for graph relations, but the accepted graph contract does not yet state this browser prerequisite or explain renderer initialization failure. The change makes the visible boundary explicit while preserving the accepted Worker-only solver and existing graph behavior.

## What Changes

- **BREAKING** Require WebGL2 for graph relation rendering and show a readable graph error when WebGL2 or renderer initialization is unavailable; do not fall back to SVG.
- Require renderer startup failure to end the current graph run, terminate its Worker, and release partial rendering resources.
- Preserve the existing graph controls, DOM node interactions, relation geometry, and memory-only coordinates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-ui`: define WebGL2 as a graph-page prerequisite and specify readable, terminal renderer startup failure.

## Impact

The graph page asset order, browser graph adapter and renderer, focused graph tests, the live workbench-ui delta, architecture, ADR 0027, product manual, glossary, Action Graph history, and changelog. No data model, API, manifest, dependency, or graph algorithm changes.
