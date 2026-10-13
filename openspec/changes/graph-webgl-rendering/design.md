## Context

Accepted PR120 is now in the live base: the browser uses the Worker-backed graph adapter, and execution failures already flow through the graph status surface. PR121 adds one WebGL2 relation renderer, but the page does not explicitly load it before the adapter, and renderer attachment happens after Worker creation. The existing graph page already displays a returned failed runtime through its readable status helper.

## Goals / Non-Goals

**Goals:**

- Make graph asset order deterministic and renderer startup failure terminal for the current graph run.
- Release Worker, renderer, and scheduled frame resources on both failed startup and normal disposal.
- Keep the current relation geometry, solver contract, DOM node interactions, and user controls.

**Non-Goals:**

- Add an SVG fallback, another rendering path, a retry loader, a dependency, or a new error API.
- Change layout algorithms, graph data, or persistence behavior.
- Optimize settled idle frames in this repair.

## Decisions

1. **Load all graph modules as parser-blocking page assets.** The graph page emits the physics core, renderer, adapter, and Workbench in that order; other pages omit the graph assets. This avoids parser timing races. A dynamic loader or retry mechanism would add a second loading path without improving the fixed page composition.
2. **Keep failure ownership in the existing adapter lifecycle.** Renderer attachment is caught by the adapter and converted into its existing failed-runtime result. The terminal stop path marks the graph failed, clears Worker callbacks, terminates the Worker, and destroys an attached renderer. `workbench.js` continues to present the error through its existing graph status helper; a separate page error API is unnecessary.
3. **Make renderer attachment clean up partial initialization before rethrowing.** The renderer owns cleanup for GL programs and buffers, its canvas and style, runtime geometry hooks, and any scheduled animation frame. The adapter then handles Worker and graph lifecycle cleanup. This keeps each resource with the module that creates it.
4. **Keep WebGL2 as the only current relation renderer.** Relationship geometry continues to come from the existing physics interface, while DOM nodes remain responsible for node labels, hit targets, selection, drag input, and accessibility. Retaining an SVG fallback would create the competing renderer that ADR 0027 explicitly excludes.

## Risks / Trade-offs

- **Browsers without WebGL2 cannot render graph relations.** The graph status and product manual state the prerequisite and failure behavior; graph data remains unchanged.
- **Initialization can fail after partial GL allocation.** Focused fake-WebGL tests verify cleanup at shader setup and at the adapter boundary; final real-browser acceptance remains a separate step.
- **A failed graph run does not retry in place.** The existing terminal Worker contract is preserved; refreshing the graph page starts a new run.

## Migration Plan

No user data or database migration is required. Ship the explicit asset order and cleanup behavior with the documented graph contract. If the renderer change must be rolled back, revert the PR121 code and contract together; no persisted graph state needs conversion.
