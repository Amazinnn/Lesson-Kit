## MODIFIED Requirements

### Requirement: Running-send preference and pending controls are explicit

The workspace's existing browser settings SHALL store the default action for a
message submitted while a turn is running, with queue as the default. The
composer SHALL retain explicit queue and interrupt-and-send choices regardless
of the configured default. A single compact pending-message list immediately above the composer SHALL show only accepted queued messages in confirmed execution order, with reorder, send-now, edit and remove controls before execution, and one continue action when retained work is paused. Interrupt handoffs SHALL NOT appear as queue entries. Pending edits
SHALL use the expected revision read with the message. The controls SHALL make
clear that an accepted pending message has not begun provider execution.

#### Scenario: Change the default running-send action

- **WHEN** the learner changes the running-send preference in workspace settings
- **THEN** the choice survives normal browser reopening and changes only future submissions

#### Scenario: Use an explicit running-send action

- **WHEN** a turn is running and the learner chooses queue or interrupt-and-send for one submission
- **THEN** that explicit action applies to the submission without changing the stored default preference

#### Scenario: Inspect and edit a pending message

- **WHEN** the learner opens an accepted message that has not started
- **THEN** its current text and order are shown, and a valid edit preserves the originally captured context

#### Scenario: Stale pending control

- **WHEN** the pending message has started or its revision changed before the learner edits or removes it
- **THEN** the UI reports that the pending state changed and refreshes the list without modifying the running message

#### Scenario: Continue paused work

- **WHEN** the conversation has retained paused messages and no provider turn is running
- **THEN** the learner can explicitly continue the queue and see the next retained message begin

#### Scenario: Interrupt result keeps older work paused

- **WHEN** D interrupts A while B and C are queued and D finishes
- **THEN** B and C remain visible as paused until the learner explicitly continues them

#### Scenario: Compact queued messages

- **WHEN** B and C are accepted with queue while A runs
- **THEN** the composer remains usable beneath one list with one compact row per message in execution order; no duplicate pending cards appear in history

#### Scenario: An empty queue is hidden

- **WHEN** no queued messages remain, including when an interrupt is waiting for stop confirmation
- **THEN** the entire queue list and its queue controls are hidden; any interrupt status is shown independently

#### Scenario: Reorder with accessible controls

- **WHEN** the learner moves C above B by dragging or the keyboard equivalent and the server accepts the expected order
- **THEN** the list and dispatch order both become C then B without changing their identities, text or captured contexts

#### Scenario: Queue reorder conflicts

- **WHEN** the queue changes before the server accepts a reorder
- **THEN** the UI refreshes the authoritative order and explains the conflict without silently persisting the stale order

#### Scenario: Send a queued message now

- **WHEN** the learner chooses send-now on queued C while A runs and B precedes C
- **THEN** C leaves the ordinary queue and uses direct interrupt-and-send with its existing identity, current text and original context; B stays paused

#### Scenario: Read long or numerous pending messages

- **WHEN** queued text is long or more than four messages are queued
- **THEN** rows offer full-text reading/editing, the list scrolls within at most four row heights, the composer stays visible, and icon actions have readable accessible names


### Requirement: Unaccepted and uncertain Agent messages remain recoverable

Before clearing the composer, the UI SHALL save outgoing text, captured request
context, and a stable submission identity in browser storage. A definite
request rejection SHALL remain visible and editable/retryable across reload.
If acceptance is uncertain, the UI SHALL distinguish that state and reconcile
by retrying the same identity and task fields. Confirmed acceptance SHALL
remove the saved local copy and display the canonical accepted message or
pending state without duplicating it in the local recovery surface. Accepted queued messages SHALL appear only in the queue list; waiting-for-stop interrupt messages SHALL have one independent send status. A retry of an accepted failed turn SHALL be an explicit linked
attempt using the current accepted message text and its originally captured
context; it SHALL NOT reuse an old queue/interrupt choice as routing metadata.
Recovery SHALL NOT overwrite a newer composer draft or automatically replay a
provider operation or its writes.

#### Scenario: The request is rejected

- **WHEN** the turn endpoint rejects a submission before acceptance
- **THEN** the original text remains recoverable after reload and retry does not replace a newer draft

#### Scenario: The acceptance response is lost

- **WHEN** the client cannot establish whether a request was accepted
- **THEN** the visible state says acceptance is uncertain and a retry uses the same identity and task fields

#### Scenario: An accepted message is queued

- **WHEN** the server confirms a message is queued or waiting for stop confirmation
- **THEN** the local outbox copy is reconciled to that accepted turn; only queued messages enter the queue list, while an interrupt waiting for stop confirmation uses its independent send status

#### Scenario: An accepted turn fails

- **WHEN** the provider fails and the conversation is reopened
- **THEN** the original accepted message and failure status remain visible; any partial output is shown only when it exists

#### Scenario: Retry an accepted failure

- **WHEN** the learner explicitly retries a failed accepted turn
- **THEN** a new turn links to the original message, uses its current accepted text and original context, and both turns remain in history

#### Scenario: Multiple local recovery records

- **WHEN** rejected, uncertain or failed-message recovery records exist
- **THEN** one compact recovery summary with a count leads to individual explicit actions, and failed accepted turns retain their inline history actions; the UI does not stack repeated full-size recovery cards above the composer or classify recovery records as queued work

#### Scenario: Interrupt submission is rejected

- **WHEN** a distinct interrupt cannot be accepted because another interrupt handoff or a Paper approval is pending
- **THEN** the text remains recoverable without overwriting a newer draft, no queue entry is created, and the UI explains the blocking state


### Requirement: Existing approval controls remain truthful and scoped
Governed Paper-reset and rollback confirmations SHALL show their exact impact and remain bound to the intended workspace/conversation/message/revision; cancellation or stale approval SHALL perform no write. Paper approval SHALL identify the existing Paper, proposed item membership/order change, and affected unfinished completion/draft counts from the existing backend preview. The Agent SHALL propose rather than apply this Paper update; a learner click SHALL cause the page to request the existing validated update. A preview snapshot or chat reply alone SHALL NOT constitute that click. This change adds no generic approval gate to ordinary tools.

Paper approval SHALL coexist with the ordinary composer. New messages explicitly submitted with queue SHALL be retained in the paused queue with their submission-time contexts. Interrupt-and-send and send-now SHALL be rejected without queue fallback or message loss; neither operation SHALL bypass the pending approval. Pending approval SHALL prevent queue continuation. Approval or cancellation SHALL leave the queue paused until the learner explicitly continues it. Existing rollback SHALL retain its composer-replacement interaction.

If the Paper or progress snapshot changed before approval, the UI SHALL perform no update, display a refreshed impact for the same proposed update and require a new approval click without requiring another Agent turn. Reload/reopen SHALL restore the pending approval and paused queue without automatic writes or provider execution. Missing/invalid targets SHALL produce actionable feedback without creating a replacement Paper. Duplicate approval attempts SHALL NOT reset progress twice.

#### Scenario: Cancel an existing Paper reset approval
- **WHEN** the learner cancels a governed Paper-reset approval or switches conversations before deciding
- **THEN** no Paper write occurs and the existing approval callback cannot act on the new conversation

#### Scenario: Approve the displayed Paper update
- **WHEN** the learner approves the current displayed Paper impact
- **THEN** the page requests the exact proposed update with its current confirmation; Paper ID, questions, historical attempts/ratings and other Papers remain unchanged, while only the target Paper's affected unfinished progress/drafts reset

#### Scenario: Continue composing while approval is pending
- **WHEN** B/C are already queued and the learner explicitly queues another message while a Paper update awaits approval
- **THEN** the composer stays usable and the new message joins the paused queue; no queued provider runs and Continue cannot bypass the approval

#### Scenario: Resolve approval before continuing the queue
- **WHEN** the learner approves or cancels the pending Paper update
- **THEN** the queue remains paused and requires explicit continuation, regardless of whether the update was approved or cancelled

#### Scenario: Practice advances before approval
- **WHEN** the learner answers more questions or the Paper changes before the approval request is validated
- **THEN** no update/reset occurs from the old confirmation, the latest impact is displayed for another click, and no additional Agent request is required

#### Scenario: Restore a pending Paper approval
- **WHEN** the learner reloads or reopens the owning conversation after a Paper approval was persisted
- **THEN** the pending decision and paused queue reappear, with no automatic update or provider launch and with impact revalidation before execution

#### Scenario: Navigate or switch conversations during approval
- **WHEN** middle navigation or a conversation switch occurs while approval is pending
- **THEN** middle navigation preserves the decision; switching conversations makes old callbacks inert, and any restored approval remains bound to its original workspace/conversation/turn/Paper/revision

#### Scenario: Repeat an approval request
- **WHEN** an approval is double-clicked or its response is lost and the decision is submitted again
- **THEN** the operation is not executed a second time and the UI does not claim a second reset

#### Scenario: Interrupt cannot bypass approval or silently queue

- **WHEN** the learner chooses interrupt-and-send or send-now while a Paper update awaits approval
- **THEN** the UI explains that approval must be resolved first, retains the composer text or original queued item, and neither starts a provider nor silently enqueues an interrupt message
