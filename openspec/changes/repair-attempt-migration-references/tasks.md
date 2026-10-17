## 1. Regression and repair
- [ ] 1.1 Reproduce the temporary-parent FK rewrite with nonempty legacy attempts/child rows and both foreign_keys entry modes.
- [ ] 1.2 Repair parent migration and already-misbound child declarations in the existing schema authority; preserve rows/IDs/unrelated schema objects and caller transaction/settings boundaries.
- [ ] 1.3 Test extra legacy columns/inbound references, idempotent reruns and missing-parent fixtures; report unresolved data violations without row fabrication/deletion.

## 2. Documentation and independent acceptance
- [ ] 2.1 Reconcile live governance spec, DATA_MODEL, Architecture and affected operator instructions; distinguish structural repair from recovery of missing learning evidence.
- [ ] 2.2 Independently run required gates and isolated migration before/after preservation checks; hand off prerequisite status to the Paper progress implementation.
- [ ] 2.3 Keep real CO repair pending unless separately authorized and proven on a copied pool; record exact remaining violations and backup provenance.
