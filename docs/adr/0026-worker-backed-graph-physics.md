# ADR 0026: Worker-backed graph physics implementation

## Status

Accepted.

## Context

ADR 0025 introduced a stable graph-physics interface and one semantic core implementation. Dense course graphs still execute every iterative solver tick on the browser main thread, where they compete with DOM/SVG painting, pointer interaction, and the ambient canvas for the same frame budget.

The execution change must preserve the module interface and the existing semantic core. It must not create a second product implementation or retain the previous main-thread solver as a runtime fallback.

## Decision

Make the Web Worker the single browser execution implementation behind `graph-physics.js`.

1. `graph-physics-core.js` is the one semantic implementation. The browser adapter and Worker both use that same core; it is not a fallback.
2. `graph-physics.js` remains the stable caller-facing module. Node/CommonJS tests export the core directly; browser callers receive a Worker-backed runtime with the same interface.
3. The browser adapter uses the core to construct the page-facing mirror state and pure geometry/query helpers. Iterative `tick()` execution happens only in `graph-physics-worker.js`.
4. The Worker imports `graph-physics-core.js`, owns iterative coordinate integration, hierarchy guides, congestion recovery, layout inflation, cooling, and settle detection, and returns revisioned snapshots.
5. The main thread owns presentation/input state: selection, hover, filters, opacity/size animation, camera, and drag/anchor input.
6. A step request carries only mutable controls required by the solver. At most one step batch is outstanding at a time.
7. Dragged or anchored coordinates remain main-thread authoritative; ordinary coordinates come from the latest non-stale Worker snapshot.
8. Large graphs preserve the existing three-ticks-per-frame intent by batching three solver ticks in one Worker request.
9. Browser environments without Worker support fail explicitly. Returning to the old execution model is a version rollback, not a runtime branch.
10. No WASM, SharedArrayBuffer, renderer replacement, graph-data change, or layout-algorithm change is included here.

## Consequences

- The graph page continues to call the same graph-physics interface while the implementation moves iterative solving off the UI thread.
- There is one semantic core and one browser execution path; no synchronous browser fallback remains.
- `/graph/model`, SQLite state, relation semantics, layout rules, graph controls, and OpenSpec capabilities remain unchanged.
- Worker protocol tests cover execution ownership and stale-snapshot rules; semantic-layout tests continue to exercise the shared core.
- Rollback is handled by Git history/release rollback rather than compatibility code carried in the current runtime.
