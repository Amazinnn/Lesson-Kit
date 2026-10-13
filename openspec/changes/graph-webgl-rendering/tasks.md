## 1. Contract and documentation

- [x] 1.1 Define WebGL2 graph rendering in the glossary before using it in formal product contracts.
- [x] 1.2 Specify the WebGL2 prerequisite, renderer failure behavior, and preserved graph behavior in the workbench-ui delta.
- [ ] 1.3 Reconcile architecture, ADR 0027, product manual, Action Graph history, and dated changelog.

## 2. Runtime repair

- [ ] 2.1 Load the renderer explicitly before the graph adapter and cover graph/non-graph page asset order.
- [ ] 2.2 Convert renderer attachment errors into the existing terminal failed-runtime status and terminate the Worker.
- [ ] 2.3 Release Worker callbacks and partial renderer GL, DOM, and animation-frame resources on failure and disposal.

## 3. Focused validation

- [ ] 3.1 Add real-adapter tests for renderer startup failure and successful WebGL painting, plus partial-resource cleanup coverage.
- [ ] 3.2 Run the focused graph Node and page-route tests, then validate the complete OpenSpec set in strict mode.
