## 1. Durable queue and worker handoff

- [ ] 1.1 Add red tests for FIFO acceptance, same-ID reconciliation after edit, and one active provider worker per conversation.
- [ ] 1.2 Persist queued turn status, immutable accepted text, current editable text, queue revision, routing action, and conversation pause state in existing JSON artifacts.
- [ ] 1.3 Dispatch ordinary queued turns after successful provider worker return; pause retained turns after failure, ordinary cancellation, or service recovery.
- [ ] 1.4 Add red tests for A/B/C/D interrupt ordering, terminal acknowledgement before D, second-interrupt conflict, post-D pause, and manual continuation.
- [ ] 1.5 Bind cancellation to the captured running turn and signal its registered provider under the conversation lock; honor cancellation before prompt delivery when process registration races with acceptance.

## 2. Pending message API

- [ ] 2.1 Add red tests for revision-checked pending edit/removal, stale revision conflicts, dispatch races, context preservation, and explicit retry of edited text.
- [ ] 2.2 Add pending edit/removal and queue-continuation handlers using existing conversation ownership and turn artifacts.
- [ ] 2.3 Verify same-ID reconciliation ignores delivery-action changes while explicit retry uses the current delivery action and original captured context.

## 3. Agent rail controls

- [ ] 3.1 Add a workspace browser setting for the default running-send action, with queue as the default and per-message queue/interrupt choices.
- [ ] 3.2 Keep the composer usable during provider execution while gating only an in-flight acceptance request.
- [ ] 3.3 Render accepted pending messages, revision-aware edit/removal controls, pause status, and explicit continuation; preserve active streaming state on queue acceptance.
- [ ] 3.4 Add focused UI tests for queued acceptance, reload restoration, pending edits/removals, preference persistence, A/D active-turn preservation, and stale mutation responses.

## 4. Contract and handoff

- [ ] 4.1 Update the affected OpenSpec, FILE_CONTRACT, Architecture, Product Manual, Action Graph, and concise STATUS handoff; do not modify DATA_MODEL unless persistent Pool fields are added.
- [ ] 4.2 Run focused conversation/API and relevant JavaScript tests, compilation/syntax checks, and strict validation of this change; report live browser and CI checks separately.
