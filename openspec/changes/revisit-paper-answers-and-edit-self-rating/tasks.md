## 1. Contract and Data design before coding

- [ ] 1.1 Audit existing review, browser feedback, Agent correction and Paper recovery paths; reconcile the explicit single-item/auto-reveal/read-only contract conflicts through this delta.
- [ ] 1.2 Define browser self-rating editing in GLOSSARY and DATA_MODEL: overwrite only the linked rating/note for the selected Paper execution; no extra feedback/attempt row, repeated learning effects, global replay or changes to other rounds. Preserve the separate Agent correction contract.
- [ ] 1.3 Reuse existing linked feedback storage and execution identity for in-place edits within this round, including earlier items. First-time rating keeps the existing flow; later edits do not reapply signals/current state/schedule. No new history-reconstruction system.

## 2. Implementation

- [ ] 2.1 Extend existing review state to all eligible items in the selected execution; independent review position, backward/forward boundaries, return-current draft retention, reload/Paper-resume recovery and completed-run handling.
- [ ] 2.2 Default reference answers and solutions to collapsed on every reviewed-item entry; show learner submission, truthful verdict and unconfirmed state without answer-key leakage.
- [ ] 2.3 Add explicit rating edit/cancel/save and reuse or minimally extend transactional Data/API mechanisms; validate exact target, stale revisions and stable retry identity; preserve failed edits.
- [ ] 2.4 Keep visible reviewed-item Agent focus accurate, preserve accepted-message context and reject cross-Paper late response contamination.
- [ ] 2.5 Synchronize PRODUCT-MANUAL and ACTION-GRAPH; reconcile affected live-contract ownership documents in the implementation PR without claiming this planning change is already delivered.

## 3. Independent acceptance and closeout

- [ ] 3.1 Deterministic regressions for at least four-item repeated navigation, return-current drafts/cursor preservation, default hidden answers on re-entry, unconfirmed submits, no-key cases, Paper switching and reload.
- [ ] 3.2 Focused Data tests for repeated in-place rating/note edits to an earlier item in this round: no added attempts/feedback rows, unchanged answers/verdicts/projections/schedule/other rounds; invalid or stale targets reject and retries do not duplicate writes.
- [ ] 3.3 Independent browser acceptance of actual controls and hidden reference material, completed-run review, score editing and failure retention using copied pools; no real-course test writes.
- [ ] 3.4 Run required pytest (PYTHONUTF8=1), official Node tests, compileall, strict live/all OpenSpec and extract-problems guard; record evidence, independently accept, then sync and archive through OpenSpec CLI.
