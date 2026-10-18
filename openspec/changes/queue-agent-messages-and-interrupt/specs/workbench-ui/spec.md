## MODIFIED Requirements

### Requirement: Agent sending is single-flight and session-bound

The Agent text composer SHALL remain editable while a turn is active. The send
action SHALL be gated only while that submission's network acceptance request
is in flight; after acceptance, later distinct messages MAY be submitted to
the same conversation's queue or explicit interrupt-and-send path. Click and
Enter SHALL share the per-request gate, including while the initial request is
awaiting its accepted turn identifier. Accepting a queued message SHALL NOT
replace the currently running turn, clear its streaming state, or reset its
activity surface. A conversation change SHALL invalidate pending approvals,
activities, polling position, and callbacks owned by the previous conversation.
Late responses from the previous conversation SHALL NOT update or act on the
newly selected conversation.

#### Scenario: Type during a running turn

- **WHEN** an Agent turn is active and the learner sends another message
- **THEN** the composer remains usable and the configured queue or explicit interrupt action is applied without starting a concurrent provider

#### Scenario: Submit twice before receiving a turn identifier

- **WHEN** the learner activates Send and then presses Enter before the first send request returns
- **THEN** only one turn-creation request is sent

#### Scenario: Accept a queued message while a turn streams

- **WHEN** a queued message is accepted while another turn is streaming
- **THEN** the active turn identity, streamed content, polling position, and Activity Float remain intact

#### Scenario: Switch sessions with pending runtime state

- **WHEN** the learner switches conversations while an activity, progress request, or approval is pending
- **THEN** the old state is cleared and any late callback is ignored without mutating or sending an action for the new conversation

#### Scenario: Progress polling fails before a terminal response

- **WHEN** the progress endpoint is temporarily unavailable while a turn is active
- **THEN** the interface keeps the active turn identity, reports unavailable progress, and does not treat the provider as failed or start a concurrent turn

### Requirement: Unaccepted and uncertain Agent messages remain recoverable

Before clearing the composer, the UI SHALL save outgoing text, captured request
context, and a stable submission identity in browser storage. A definite
request rejection SHALL remain visible and editable/retryable across reload.
If acceptance is uncertain, the UI SHALL distinguish that state and reconcile
by retrying the same identity and task fields. Confirmed acceptance SHALL
remove the saved local copy and display the canonical accepted message or
pending state. A retry of an accepted failed turn SHALL be an explicit linked
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
- **THEN** the local outbox copy is reconciled to that accepted turn and the pending list shows its current text and status

#### Scenario: An accepted turn fails

- **WHEN** the provider fails and the conversation is reopened
- **THEN** the original accepted message and failure status remain visible; any partial output is shown only when it exists

#### Scenario: Retry an accepted failure

- **WHEN** the learner explicitly retries a failed accepted turn
- **THEN** a new turn links to the original message, uses its current accepted text and original context, and both turns remain in history

### Requirement: Running-send preference and pending controls are explicit

The workspace's existing browser settings SHALL store the default action for a
message submitted while a turn is running, with queue as the default. The
composer SHALL retain explicit queue and interrupt-and-send choices regardless
of the configured default. A pending-message list SHALL show accepted text,
order, and paused or waiting status, with edit/remove controls only before
execution and a continue action when retained work is paused. Pending edits
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
