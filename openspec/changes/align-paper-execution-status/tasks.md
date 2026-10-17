## 1. Shared state and contracts

- [x] 1.1 Audit Data summary/read/start/parked paths and define one shared continuation result without UI business-rule duplication; reconcile affected contracts and glossary before coding. Existing glossary terms cover the behavior; no new design noun was added.
- [x] 1.2 Fix mismatched progress attachment in saved Paper reads and expose continuation reasons consistently with active/parked start checks.

## 2. UI consistency

- [x] 2.1 Use backend state in list and practice entry points; distinguish old execution from current container, translate errors and fold long missing-ID details.
- [x] 2.2 Keep valid rename/export/delete actions independent from continuation; refresh stale status after rejected actions without discarding drafts or evidence.
- [x] 2.3 Synchronize PRODUCT-MANUAL/ACTION-GRAPH and actual affected API/architecture/data contracts in the implementation PR.

## 3. Acceptance

- [x] 3.1 Deterministic tests: count mismatch, same-count identity/order mismatch, unavailable questions, active and parked states, valid continuation and stale actions.
- [ ] 3.2 Independent isolated browser/API acceptance: consistent progress, labels, controls and non-destructive failure; no real-course test writes.
- [ ] 3.3 Required Python/Node/compileall/OpenSpec/extraction checks, evidence handoff and independent acceptance before CLI archive. Planning completeness does not complete these tasks.
