## 1. Durable queue and worker handoff

- [x] 1.1 Add red tests for FIFO acceptance, same-ID reconciliation after edit, and one active provider worker per conversation — focused conversation/API tests pass.
- [x] 1.2 Persist queued turn status, immutable accepted text, current editable text, queue revision, routing action, and conversation pause state in existing JSON artifacts — source commit `f1481580`.
- [x] 1.3 Dispatch ordinary queued turns after successful provider worker return; pause retained turns after failure, ordinary cancellation, or service recovery — focused conversation/API tests pass.
- [x] 1.4 Add red tests for A/B/C/D interrupt ordering, terminal acknowledgement before D, second-interrupt conflict, post-D pause, and manual continuation — focused conversation/API tests pass.
- [x] 1.5 Bind cancellation to the captured running turn and signal its registered provider under the conversation lock; honor cancellation before prompt delivery when process registration races with acceptance — Pi no-ack barrier and prompt-lock tests pass in `c9d05d15`.

## 2. Pending message API

- [x] 2.1 Add red tests for revision-checked pending edit/removal, stale revision conflicts, dispatch races, context preservation, and explicit retry of edited text — focused conversation/API tests pass.
- [x] 2.2 Add pending edit/removal and queue-continuation handlers using existing conversation ownership and turn artifacts — source commit `f1481580`.
- [x] 2.3 Verify same-ID reconciliation ignores delivery-action changes while explicit retry uses the current delivery action and original captured context — focused conversation/API tests pass.

## 3. Agent rail controls

- [x] 3.1 Add a workspace browser setting for the default running-send action, with queue as the default and per-message queue/interrupt choices — official Node tests pass.
- [x] 3.2 Keep the composer usable during provider execution while gating only an in-flight acceptance request — official Node tests and isolated Chromium smoke pass.
- [x] 3.3 Render accepted pending messages, revision-aware edit/removal controls, pause status, and explicit continuation; preserve active streaming state on queue acceptance — official Node tests and isolated Chromium smoke pass.
- [x] 3.4 Add focused UI tests for queued acceptance, reload restoration, pending edits/removals, preference persistence, A/D active-turn preservation, and stale mutation responses — official Node tests and isolated Chromium smoke pass.

## 4. Contract and handoff

- [x] 4.1 Update affected OpenSpec, Architecture, Product Manual, Action Graph, and concise STATUS handoff. FILE_CONTRACT and GLOSSARY already cover the queue artifacts and terms; no Pool fields were added, so DATA_MODEL is unchanged.
- [x] 4.2 Focused conversation/API, official JavaScript, compileall, extraction guard, strict OpenSpec, and isolated Chromium checks pass; full Python PR CI is reported separately in STATUS.
