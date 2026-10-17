## 1. Contracts and storage boundary
- [ ] 1.1 Reconcile the proposed glossary, live specs, DATA_MODEL, affected FILE_CONTRACT, Architecture, Product Manual and Action Graph in the implementation PR; preserve existing scenarios.
- [ ] 1.2 Add Data-owned per-Paper unfinished progress/drafts and a separate selected execution; migrate healthy legacy state on an isolated copy, preserving attempts, ratings and schedule rows.
- [ ] 1.3 Resolve the separate legacy attempt-FK repair before accepting migration on affected pools; report existing missing-parent rows explicitly.

## 2. Resume and rendering
- [ ] 2.1 Make switching A to B to A pause/resume independently; retain unsubmitted text/choices and cursor across refresh/restart, with no implicit abandonment or need to finish A first.
- [ ] 2.2 Reuse per-item choice/judgment/open renderers, keep rating timing compatible, and prevent duplicate attempt/feedback writes during resume.

## 3. Governed updates and deletion
- [ ] 3.1 Reuse explicit-ID Paper updates and question patches; add impact preview/confirmation for manual Paper structure changes and no-op/metadata preservation.
- [ ] 3.2 Apply semantic question edits through common Data rules to reset only affected unfinished items/drafts; enforce stale-submit rejection before any learning write across supported writers and tabs.
- [ ] 3.3 Implement Paper-only deletion and question current-reference cleanup; preserve other-item progress, history and genuine learning evidence, including empty/deleted containers.
- [ ] 3.4 Keep invalid containers visible and repairable without treating their missing items as startable; document CLI/Agent update versus create behavior and return truthful receipts.

## 4. Independent acceptance
- [ ] 4.1 Prove reset boundaries with before/after learning-table preservation assertions and fault-injection checks; demonstrate stale request zero-write behavior.
- [ ] 4.2 Run the required Python, official JS, compileall, strict all-OpenSpec and extraction-guard gates on exact candidate heads.
- [ ] 4.3 Independently walk through switching multiple unfinished Papers, mixed types, semantic correction and deletion in a copied pool; record limitations and handoff.
- [ ] 4.4 Plan any real CO recovery separately using verified backups/mappings and explicit approval; do not mark it complete from this feature's tests or fabricate attempts.
