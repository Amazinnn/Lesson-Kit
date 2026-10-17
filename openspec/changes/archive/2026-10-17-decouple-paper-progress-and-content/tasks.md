## 1. Contracts and storage boundary
- [x] 1.1 Reconcile the proposed glossary, live specs, DATA_MODEL, affected FILE_CONTRACT, Architecture, Product Manual and Action Graph in the implementation PR; preserve existing scenarios.
- [x] 1.2 Add Data-owned per-Paper unfinished progress/drafts and a separate selected execution; migrate healthy legacy state on an isolated copy, preserving attempts, ratings and schedule rows.
- [x] 1.3 Resolve the separate legacy attempt-FK repair before accepting migration on affected pools; report existing missing-parent rows explicitly.

## 2. Resume and rendering
- [x] 2.1 Make switching A to B to A pause/resume independently; retain unsubmitted text/choices and cursor across refresh/restart, with no implicit abandonment or need to finish A first.
- [x] 2.2 Reuse per-item choice/judgment/open renderers, keep rating timing compatible, and prevent duplicate attempt/feedback writes during resume.
- [x] 2.3 Remove the owner-rejected standalone AI explanation presentation and deduplicate repeated explanation text without deleting content/provenance fields.

## 3. Governed updates and deletion
- [x] 3.1 Reuse explicit-ID Paper updates and question patches; add impact preview/confirmation for manual Paper structure changes and no-op/metadata preservation.
- [x] 3.2 Apply semantic question edits through common Data rules to reset only affected unfinished items/drafts; enforce stale-submit rejection before any learning write across supported writers and tabs.
- [x] 3.3 Implement Paper-only deletion and question current-reference cleanup; preserve other-item progress, history and genuine learning evidence, including empty/deleted containers.
- [x] 3.4 Keep invalid containers visible and repairable without treating their missing items as startable; document CLI/Agent update versus create behavior and return truthful receipts.

## 4. Independent acceptance
- [x] 4.1 Prove reset boundaries with before/after learning-table preservation assertions and fault-injection checks; demonstrate stale request zero-write behavior.
- [x] 4.2 Run the required Python, official JS, compileall, strict all-OpenSpec and extraction-guard gates on exact candidate heads.
- [x] 4.3 Independently walk through switching multiple unfinished Papers, mixed types, semantic correction and deletion in a copied pool; record limitations and handoff.
- [x] 4.4 Record real CO recovery as separate blocked work requiring verified backups/mappings and explicit approval; do not claim recovery from this feature's tests or fabricate attempts. See STATUS-paper-progress-2026-10-17.md.
