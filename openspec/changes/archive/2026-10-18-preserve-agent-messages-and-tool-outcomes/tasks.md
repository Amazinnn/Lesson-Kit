## 1. Accepted-message history and idempotency

- [x] 1.1 Persist submitted message/context and optional identity in the existing turn artifact before dispatch; resolve repeated identities and reject changed payloads.
- [x] 1.2 Merge accepted turns into history without duplicating successful legacy transcript pairs; preserve actual partial output and terminal failure status.
- [x] 1.3 Add deterministic bridge/API coverage for provider failure, same-ID retry/conflict, context stability, and legacy history.

## 2. Local send recovery and activity cards

- [x] 2.1 Persist outgoing identity/text/context before composer clearing; restore rejected or uncertain sends across reload without replacing a newer draft.
- [x] 2.2 Reconcile uncertain acceptance with the same identity; make accepted-failure retry explicit and linked to the original turn.
- [x] 2.3 Render semantic activity state/outcome and evidenced impact with folded redacted diagnostics; expose only supported recovery controls.
- [x] 2.4 Add focused UI tests for rejection, uncertainty, provider failure/history reload, and activity-card evidence.

## 3. Contract handoff

- [x] 3.1 Update `FILE_CONTRACT.md`, `docs/GLOSSARY.md`, the relevant `docs/PRODUCT-MANUAL.md` section, and `docs/ACTION-GRAPH.md`.
- [x] 3.2 Run focused Python and JavaScript checks plus strict validation for this change.
