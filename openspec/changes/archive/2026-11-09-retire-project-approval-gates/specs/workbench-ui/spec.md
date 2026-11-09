## REMOVED Requirements

### Requirement: Low-reversibility rollback requires an Approval Gate

**Reason**: The owner explicitly cancels project approvals in Q098/S008.
**Migration**: Use direct-project-actions. Validate the actual operation input, reconcile legacy pending state once and remove approval-driven UI and dispatch pauses.

### Requirement: Existing approval controls remain truthful and scoped

**Reason**: The owner explicitly cancels project approvals in Q098/S008.
**Migration**: Use direct-project-actions. Validate the actual operation input, reconcile legacy pending state once and remove approval-driven UI and dispatch pauses.

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


Project approval SHALL be retired. Any persisted legacy pending approval SHALL be reconciled under direct-project-actions and SHALL NOT block dispatch solely for approval. All unrelated identity, single-flight, stop-handoff and context constraints SHALL remain applicable.

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

- **WHEN** a request encounters a legacy pending approval state
- **THEN** that state is reconciled without an approval gate and the requested operation follows normal identity, ownership and concurrency rules without approval-driven blocking

#### Scenario: Progress polling fails before a terminal response

- **WHEN** the progress endpoint is temporarily unavailable while a turn is active
- **THEN** the interface keeps the active turn identity, reports unavailable progress, and does not treat the provider as failed or start a concurrent turn


### Requirement: Scrollable Agent conversation

The Agent chat SHALL constrain its message region to the available column height and allow normal mouse-wheel vertical scrolling when messages exceed that height.


Project approval SHALL be retired. Any persisted legacy pending approval SHALL be reconciled under direct-project-actions and SHALL NOT block dispatch solely for approval. All unrelated identity, single-flight, stop-handoff and context constraints SHALL remain applicable.

#### Scenario: Read long conversation

- **WHEN** the Agent message list is taller than the visible right column
- **THEN** the learner can scroll the message region with the mouse wheel while the input remains available

#### Scenario: Read long cards while chatting

- **WHEN** a request encounters a legacy pending approval state
- **THEN** that state is reconciled without an approval gate and the requested operation follows normal identity, ownership and concurrency rules without approval-driven blocking


### Requirement: Content results expose type, source, and rollback state

Normal content-result presentation SHALL show a concise truthful result through the existing conversation, without default source, reason or rollback-state fields and without explicit successful-batch undo controls. Detailed counts, provenance and per-item failures SHALL remain available in CLI receipts and verification artifacts. Historical records SHALL remain accurate and user-requested explanations SHALL match actual writes.

#### Scenario: Source problem enters automatically

- **WHEN** a governed content result is rendered or reopened
- **THEN** its actual outcome is represented once with the minimal normal presentation, no rollback action, and detailed evidence available through the existing retrieval path

#### Scenario: Reopen a rolled-back result

- **WHEN** a governed content result is rendered or reopened
- **THEN** its actual outcome is represented once with the minimal normal presentation, no rollback action, and detailed evidence available through the existing retrieval path

#### Scenario: Generated explanation repeats the normal explanation

- **WHEN** a governed content result is rendered or reopened
- **THEN** its actual outcome is represented once with the minimal normal presentation, no rollback action, and detailed evidence available through the existing retrieval path

