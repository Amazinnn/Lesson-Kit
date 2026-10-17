## 1. Regression and repair
- [x] 1.1 Reproduce the temporary-parent FK rewrite with nonempty legacy attempts/child rows and both foreign_keys entry modes.
- [x] 1.2 Repair parent migration and already-misbound child declarations in the existing schema authority; preserve rows/IDs/unrelated schema objects and caller transaction/settings boundaries.
- [x] 1.3 Test extra legacy columns/inbound references, idempotent reruns and missing-parent fixtures; report unresolved data violations without row fabrication/deletion.

## 2. Documentation and independent acceptance
- [x] 2.1 Reconcile live governance spec, DATA_MODEL, Architecture and affected operator instructions; distinguish structural repair from recovery of missing learning evidence.
- [x] 2.2 Acceptance closed by the owner on 2026-10-17 after normal Physics Paper display, submission and reload/continuation were confirmed. Supporting evidence includes the recorded isolated migration preservation comparisons and the independently verified integrated 1049-test suite/205 Node tests at main 263e0687. This records owner acceptance, not a newly performed independent migration run.
- [x] 2.3 Keep real CO repair pending unless separately authorized and proven on a copied pool; record exact remaining violations and backup provenance.
- [x] 2.4 Perform owner-requested real-course-copy acceptance with isolated registry/port: compare rows and unrelated schema, reproduce the Physics Paper failure, migrate the copy, exercise answer/feedback and restart recovery; record actual effects and unresolved CO references.
- [x] 2.5 With explicit owner authorization, back up and migrate the original Physics pool after fresh-copy verification; compare all existing rows, validate integrity and foreign keys, and verify production service read-back without submitting practice answers.
- [x] 2.6 With explicit owner authorization, audit every registered formal course pool, migrate outdated pools only after copy validation and backup, preserve learning/content rows, and record remaining violations and production read-back.

Implementation handoff: `docs/STATUS-attempt-reference-repair-2026-10-17.md`.
Task 2.3: the owner subsequently authorized all formal course migrations; CO structural migration and a fresh backup are verified. The original 19 missing attempts remain explicitly reported and are not fabricated or deleted. See `docs/audits/2026-10-17-all-course-live-migration.md` for exact evidence and backup provenance.
Task 2.2 was subsequently taken over by the owner, who confirmed the proposed normal-use acceptance with no issues on 2026-10-17.
Real-copy acceptance evidence: `docs/audits/2026-10-17-attempt-real-copy-acceptance.md`. It supplements fixture checks and does not authorize writes to the original course pools.
