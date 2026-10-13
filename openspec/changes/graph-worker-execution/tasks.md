## 1. Contract

- [x] 1.1 Reuse the existing Web Worker term from ADR 0026 and complete the proposal, workbench-ui delta, and design through the installed OpenSpec workflow.

## 2. Runtime repair

- [ ] 2.1 Emit the graph core before the adapter on graph pages and verify non-graph pages omit both scripts.
- [ ] 2.2 Keep the synchronous core private in browser pages and expose only the Worker-backed adapter.
- [ ] 2.3 Make Worker construction, posting, and asynchronous errors terminal: terminate once, clear pending work, prevent retries and reheating.
- [ ] 2.4 Surface unsupported or failed graph execution through the existing readable status and stop solver-frame scheduling.
- [ ] 2.5 Preserve successful step behavior, stale-snapshot rejection, drag authority, normal-settle status, and memory-only coordinates.

## 3. Contract reconciliation and verification

- [ ] 3.1 Update architecture, ADR 0026, product manual, and dated changelog; check Action Graph, DATA_MODEL, and FILE_CONTRACT responsibilities and edit only if affected.
- [ ] 3.2 Add focused adapter regressions for unsupported Worker, one terminal failure with no later posts, successful stepping, and existing snapshot/drag rules.
- [ ] 3.3 Add the focused graph-route script-order regression and run the associated Python and graph Node checks.
- [ ] 3.4 Run strict OpenSpec validation for all specs and record exact commands and outcomes in the central PR120 report.
