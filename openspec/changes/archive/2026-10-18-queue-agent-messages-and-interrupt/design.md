## Context

See `proposal.md` for motivation and `specs/` for observable requirements. `workbench.bridge.conversations` already owns accepted turn artifacts, the per-conversation reentrant lock, provider worker lifecycle, and cancellation. The UI already stores workspace-scoped preferences in `wb_settings_<workspace>` and keeps the Agent rail mounted across same-workspace navigation.

## Goals / Non-Goals

**Goals:** Reuse turn files as the durable queue, keep acceptance and dispatch under existing conversation ownership, and let the running browser turn remain independent from later queued submissions.

**Non-Goals:** Add a scheduler, queue database/index, SQLite fields, provider pause/resume, provider replay, or changes to the independent Paper approval work.

## Decisions

1. **Use accepted turn artifacts as the queue.** Each turn file remains the durable message record. Numeric `turn-NNN` order defines FIFO; an interrupt submission is selected ahead of ordinary queued messages only when its recorded `interrupt_target_turn_id` matches the turn that just reached terminal status. This avoids a second queue index that could drift from accepted messages. `conversation.json` gains one `queue_paused` flag; missing on older records means false.

2. **Separate accepted identity from editable text.** Turn artifacts retain immutable `accepted_message` and task fields for same-identity reconciliation, while `message` is the current text used at execution and history. `queue_revision` starts at 1 and increments after each accepted pending edit. Delivery action (`queue` or `interrupt`) is stored as routing metadata but excluded from stable task-field comparison; explicit retries use the current UI choice and the original turn context.

3. **Expose the existing turn API with small queue operations.** `POST .../turns` accepts optional `queue_action` (`queue` by default, or `interrupt`). `PATCH .../turns/{turn_id}` edits a pending message with `expected_revision`; `DELETE` on that route retains a cancelled history entry and also requires `expected_revision`. `POST .../queue/continue` explicitly resumes retained work. Session reads expose pending user messages, their revisions and queue state; captured context remains private.

4. **Bind cancellation and handoff to one captured turn.** Under `_LOCK`, accepting interrupt D records its target A, marks the retained queue paused, adds cancellation to A's `(conversation, turn)` key, and signals only A's captured process without waiting. If A's process has not registered yet, its worker checks the same cancellation key before sending a prompt and immediately after registration. A second distinct interrupt while one is waiting receives 409. The worker wrapper dispatches after `_run_turn` returns, so normal process exit and Pi RPC settlement/cleanup precede D. A normal terminal result racing with the abort still hands off to D because the priority intent names A.

5. **Continue through the existing worker, never the browser.** After an ordinary successful turn, `_run_turn_safely` starts the next queued turn if the queue is open. A failure, ordinary cancellation, or service recovery sets `queue_paused`; an interrupt target may run after its captured turn terminates, but older messages stay paused after it. Explicit continuation starts the next eligible retained turn. A new message accepted while older work is paused remains queued.

6. **Keep queue acceptance outside the live turn controller.** The running-send preference lives beside existing learner settings. The composer can select its saved default or explicitly choose queue/interrupt for one message. A queued response updates the pending list and outbox reconciliation without resetting the active turn, stream, poll, or Activity Float. The pending list uses the session's accepted user-message projections and mutation endpoints rather than a second browser-side queue.

## Risks / Trade-offs

- **[A worker exits between interrupt acceptance and cancellation signalling]** → Persist the target and signal its captured process under the same `_LOCK` used by terminal handoff; only the worker that owns that turn may report its terminal state.
- **[A service restart leaves a waiting interrupt message]** → Recovery marks the running turn interrupted, retains the interrupt message as pending, pauses the queue, and requires explicit continuation.
- **[A stale browser edits after dispatch]** → Check turn status and expected revision under `_LOCK`; return 409 and let the browser reload the pending list.
- **[Older turn artifacts lack queue fields]** → Read `message` as their original accepted text and treat absent queue/revision fields as the idle, unedited legacy state.

## Migration Plan

No database migration is needed. New queue fields are written only to existing conversation and turn JSON. Older records remain readable; the feature is served by the same workbench process and can be rolled back by restoring the prior code while retaining readable turn files and ignoring additive fields.
