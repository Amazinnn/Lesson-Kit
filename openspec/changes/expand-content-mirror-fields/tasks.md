## 1. Contract

- [x] 1.1 Add and validate the scoped OpenSpec proposal and behavior delta before production edits.
- [x] 1.2 Reconcile the existing mirror field, writer/consumer, architecture, product, action, glossary, and changelog contracts.

## 2. Regression cases

- [x] 2.1 Add temporary-fixture cases for invalid KP/problem figure references and assert check/sync leave pool, JSON, state, and log unchanged.
- [x] 2.2 Add old-v1 remote adoption, one-time no-op, revision-spoof, wrong-revision, and divergent-edit cases.
- [x] 2.3 Add full, absent, and partial difficulty-schema cases, including explicit-rating rejection and content-edit check/sync agreement.

## 3. Minimal source repair

- [x] 3.1 Reuse figure_mirror's existing path rules to validate both projections during the read-only content-mirror plan.
- [x] 3.2 Reuse data.difficulty.check for explicit ratings and limit stale clears and SQL updates to present fields.
- [x] 3.3 Adopt only a complete matching projection at the exact next revision through the existing convergence path.

## 4. Focused acceptance and handoff

- [x] 4.1 Run the requested focused RED/GREEN regressions, existing mirror/difficulty/figure/API tests, and strict OpenSpec validation.
- [ ] 4.2 Record exact commits, commands, outcomes, and remaining independent acceptance gates in the PR123 fix report.
