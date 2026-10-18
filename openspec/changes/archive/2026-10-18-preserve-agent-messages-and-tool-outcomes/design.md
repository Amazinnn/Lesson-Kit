## Scope and decisions

The broader message-lifecycle investigation and queue/approval decisions remain in [`complete-agent-message-lifecycle/design.md`](../complete-agent-message-lifecycle/design.md). This change owns only accepted-message durability and truthful activity outcomes.

1. Store `message`, the originally built server context, optional `submission_id`, and the normalized submitted fields on the existing turn JSON before starting its worker. Compare a duplicate identity against those submitted fields, not freshly rebuilt server enrichment; return the original turn when they match and reject a conflict. The ID is an opaque caller value; no hash is needed.
2. Build history from accepted turn artifacts plus legacy successful transcript entries. Use `turn_id` to show a successful turn once. A failed turn keeps its actual public partial output and terminal status; absent output stays absent.
3. Save the outgoing message and captured request fields to browser storage before clearing the composer. A rejected request stays editable/retryable; a request with uncertain acceptance is retried with its original identity. Clear the local outbox only after confirmed acceptance, and never place an older recovered message into a newer draft.
4. Keep accepted failure retry explicit and linked to the original turn. Do not retry a provider tool operation or replay writes automatically.
5. Build activity cards from normalized activity evidence. Unknown impact stays unknown. Folded diagnostics use the existing redaction and concise-summary rules. Do not add controls for unsupported selective recovery.
