## Context

See proposal.md for motivation and specs/workbench-ui/spec.md for the user-visible contract. The graph core currently assigns its CommonJS semantic implementation to the browser global GraphPhysics. The public adapter writes a core script dynamically and immediately reads that global, while the graph page includes the adapter before workbench.js. Worker errors currently clear the pending-step flag but leave the runtime eligible to post another step. The fix must keep the semantic core and successful graph interface unchanged.

## Goals / Non-Goals

**Goals:**

- Make the graph page load the core and adapter in a deterministic parser order.
- Ensure graph UI code accepts only the Worker-backed adapter as its public physics module.
- End a failed runtime once, terminate its Worker, prevent later posts or reheating, and show a persistent readable graph status.
- Keep the graph model, semantic layout, worker message contract, and memory-only coordinates intact.

**Non-Goals:**

- Change graph physics algorithms, worker protocol shape, graph data, APIs, or persisted fields.
- Add a synchronous fallback, dynamic loader, retries, new browser dependency, or a new product action.
- Change the knowledge-figures layout contract; its semantic layout and non-persistence rules remain authoritative there.

## Decisions

1. **Load graph scripts explicitly on graph pages.** In the server page shell, emit graph-physics-core.js, then graph-physics.js, then workbench.js only when graph_mode is enabled. The adapter requires the core to be present and does not use document.write. This uses the parser's existing ordered-script behavior and avoids a loader abstraction or callback race. A focused route test checks order and confirms ordinary pages omit both graph scripts.

2. **Keep the semantic core private to the adapter after loading.** The adapter captures the parser-loaded core and removes its global GraphPhysics binding before checking Worker support. It publishes GraphPhysics only after creating the Worker-backed adapter API; the API carries a small marker so workbench.js can reject the synchronous core if the adapter script itself did not become available. CommonJS continues exporting the same core for semantic tests, and the Worker continues importing that same core. Changing core or worker source would widen ownership without changing semantic behavior.

3. **Treat Worker errors as one terminal runtime transition.** A single failure path marks the runtime failed, clears pending and unapplied snapshots, sets alpha to zero, terminates the Worker, and stores one readable error on the runtime. Posting, snapshot application, tick, and reheat paths check that state. Disposal remains safe after failure. Worker construction or an initial/postMessage exception follows the same path so the page can report startup failures as well as asynchronous errors.

4. **Let the graph page own presentation and animation cleanup.** Before requesting graph data, workbench.js checks for the Worker-backed API and reports unsupported or missing-resource errors through the existing graph status surface. When a runtime fails, the next pending graph frame sets the failed status directly, clears pending solver dirty work, and returns without rescheduling. Ambient graph decoration keeps its current lifecycle. This explicit status update does not depend on the solving-state edge comparison, which can miss a transition when alpha is already zero at frame start.

5. **Keep the capability delta in workbench-ui.** That spec owns page availability and user-visible failure behavior. knowledge-figures continues to own graph semantics and memory-only coordinates, so no duplicate or overriding requirement is added there. DATA_MODEL and FILE_CONTRACT are unaffected because this change adds no durable state or intermediate artifact.

## Risks / Trade-offs

- A graph page with unavailable Worker support or a failed Worker remains unavailable until reload. This is the required terminal behavior and is stated in the graph status.
- One animation frame may already be queued when an asynchronous error arrives. The failed-state guard consumes that wakeup and schedules no further solver frame; ambient graph decoration keeps its current lifecycle.
- If graph script loading fails, the route test can verify intended order but cannot emulate browser network failure. The adapter and UI checks cover the resulting missing API; final browser acceptance is a separate boundary.

## Migration Plan

No database or file migration is needed. Deploy the page ordering, adapter, and UI handling together. Roll back the code and its OpenSpec change together through version control if a release must restore the prior graph behavior; no user data is rewritten.

## Open Questions

None.
