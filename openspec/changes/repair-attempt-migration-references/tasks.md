## 1. Regression and repair
- [x] 1.1 Reproduce the temporary-parent FK rewrite with nonempty legacy attempts/child rows and both foreign_keys entry modes.
- [x] 1.2 Repair parent migration and already-misbound child declarations in the existing schema authority; preserve rows/IDs/unrelated schema objects and caller transaction/settings boundaries.
- [x] 1.3 Test extra legacy columns/inbound references, idempotent reruns and missing-parent fixtures; report unresolved data violations without row fabrication/deletion.

## 2. Documentation and independent acceptance
- [x] 2.1 Reconcile live governance spec, DATA_MODEL, Architecture and affected operator instructions; distinguish structural repair from recovery of missing learning evidence.
- [ ] 2.2 Independently run required gates and isolated migration before/after preservation checks; hand off prerequisite status to the Paper progress implementation.
- [ ] 2.3 Keep real CO repair pending unless separately authorized and proven on a copied pool; record exact remaining violations and backup provenance.
- [x] 2.4 Perform owner-requested real-course-copy acceptance with isolated registry/port: compare rows and unrelated schema, reproduce the Physics Paper failure, migrate the copy, exercise answer/feedback and restart recovery; record actual effects and unresolved CO references.

Implementation handoff: `docs/STATUS-attempt-reference-repair-2026-10-17.md`.
Task 2.3 records the pending boundary and existing dated evidence only; no real CO repair or fresh backup validation was performed.
Task 2.2 remains pending for the user's independently assigned acceptance Agent.
Real-copy acceptance evidence: `docs/audits/2026-10-17-attempt-real-copy-acceptance.md`. It supplements fixture checks and does not authorize writes to the original course pools.
