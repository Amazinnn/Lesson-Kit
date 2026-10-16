## ADDED Requirements

### Requirement: Agent rail presentation keeps the learning page primary

The Agent rail SHALL remain a conversation surface within the existing workbench shell, and the current Lesson Kit page SHALL remain the primary learning surface. The rail SHALL show compact chips for the current page and available page context without changing the context sent to the provider. Its text composer SHALL grow to fit entered text within the rail. Agent presentation SHALL reuse the existing workbench visual tokens; an idle rail SHALL NOT leave an auxiliary work surface open.

#### Scenario: Read the current Agent context

- **WHEN** the learner opens an Agent conversation on a workbench page
- **THEN** the rail shows the current page and available page context as compact chips while the current Lesson Kit page remains visible

#### Scenario: Enter a longer message

- **WHEN** the learner enters multiple lines in the Agent composer
- **THEN** the composer grows to show the entered text without replacing the conversation with a task dashboard

#### Scenario: No runtime activity is present

- **WHEN** the Agent is idle and no Artifact preview is active
- **THEN** the central page remains unobstructed by an Activity Float or Bottom Dock

### Requirement: Agent runtime work uses transient auxiliary surfaces

Short provider activity SHALL use a replaceable Activity Float that presents the latest activity. Sustained multi-step activity SHALL use a temporary Bottom Dock that presents current milestones and latest status while the Agent rail remains usable. These surfaces SHALL NOT replace the existing conversation activity or execution history, accumulate as a separate task history, or expose a raw provider-event wall. A confirmed failure SHALL show a concise semantic summary while detailed output remains behind the existing collapsed disclosure. A failed progress read SHALL be represented as unavailable progress, not as proof that the provider turn failed.

#### Scenario: A short activity is visible

- **WHEN** a provider reports a short activity
- **THEN** the Activity Float shows its readable label and current state, and a later short activity replaces that float content

#### Scenario: Work continues across milestones

- **WHEN** a provider reports sustained multi-step work
- **THEN** the Bottom Dock shows the current milestones and latest status while the conversation remains available in the Agent rail

#### Scenario: Detailed output is available

- **WHEN** an activity includes provider output
- **THEN** the transient surface keeps the semantic summary visible and the detailed output remains behind the existing closed disclosure in the conversation

#### Scenario: A provider confirms a failure

- **WHEN** the provider reports that the current turn failed
- **THEN** the work surface shows a concise failure summary and retains detailed output behind the existing closed disclosure

#### Scenario: Progress cannot be read

- **WHEN** a progress request fails while the provider turn has no authoritative terminal status
- **THEN** the interface reports that progress is unavailable, keeps the current turn gated against another send, and does not label the provider turn as failed

### Requirement: Explicit collapse applies to the current Agent turn

When the learner collapses an auxiliary work surface, later activity updates and Artifacts in the same user turn SHALL NOT automatically reopen an auxiliary surface. A new user turn SHALL reset this suppression. An explicit Preview action on an Artifact MAY reopen its Adaptive Split. Switching to another conversation SHALL clear the prior conversation's transient surfaces and collapse state.

#### Scenario: Collapse while work is running

- **WHEN** the learner collapses the Activity Float or Bottom Dock during a user turn and another activity arrives
- **THEN** the new activity remains in the conversation history and no auxiliary surface automatically reopens for that turn

#### Scenario: Start a later user turn

- **WHEN** the learner sends a new message after the previous turn has ended
- **THEN** automatic auxiliary-surface presentation is enabled for the new turn

#### Scenario: Switch conversations

- **WHEN** the learner opens a different conversation
- **THEN** no activity surface or collapse state from the previous conversation appears in the new one

### Requirement: Agent sending is single-flight and session-bound

The Agent text composer SHALL remain editable while a turn is active, but the send action SHALL be gated from the first submit attempt until the current request is rejected or its turn reaches an authoritative terminal state. Click and Enter submission SHALL share this gate, including while the initial send request is awaiting its turn identifier. A conversation change SHALL invalidate pending approvals, activities, polling position, and callbacks owned by the previous conversation. Late responses from the previous conversation SHALL NOT update or act on the newly selected conversation.

#### Scenario: Type during a running turn

- **WHEN** an Agent turn is active
- **THEN** the learner can continue editing the composer, but Send and Enter cannot submit another turn

#### Scenario: Submit twice before receiving a turn identifier

- **WHEN** the learner activates Send and then presses Enter before the first send request returns
- **THEN** only one turn-creation request is sent

#### Scenario: Switch sessions with pending runtime state

- **WHEN** the learner switches conversations while an activity, progress request, or approval is pending
- **THEN** the old state is cleared and any late callback is ignored without mutating or sending an action for the new conversation

#### Scenario: Progress polling fails before a terminal response

- **WHEN** the progress endpoint is temporarily unavailable while a turn is active
- **THEN** the interface keeps the active turn identity and send gate, and reports unavailable progress without creating a retry turn

### Requirement: Low-reversibility rollback requires an Approval Gate

An Agent-triggered content-batch rollback SHALL require an Approval Gate before the existing rollback operation is called. The gate SHALL identify the batch, explain the reason and impact, and replace the normal composer until the learner approves or cancels. Approval SHALL call the existing rollback operation once. Cancellation SHALL restore the composer without issuing a rollback request. Ordinary reversible provider activity SHALL NOT use this gate. A conversation change SHALL invalidate any approval callback from the prior conversation.

#### Scenario: Review a rollback request

- **WHEN** the learner selects the rollback control on a content-batch result
- **THEN** the Approval Gate replaces the composer and identifies the batch and the effect of rollback

#### Scenario: Approve rollback

- **WHEN** the learner approves the displayed rollback
- **THEN** the existing rollback operation is issued once for the displayed batch

#### Scenario: Cancel rollback

- **WHEN** the learner cancels the displayed rollback
- **THEN** the composer returns and no rollback request is issued

#### Scenario: Switch conversations while approval is open

- **WHEN** the learner changes conversations before deciding on a rollback
- **THEN** the gate closes and its old callback cannot roll back the prior batch

### Requirement: Managed Paper Artifacts remain explicit handoffs

The conversation SHALL render a Paper Artifact only from a validated managed-Paper action. Its identity, title, and item count SHALL be supplied from the matching managed Paper record, not trusted from model text. A new Artifact SHALL appear as one conversation card with its managed identity, title, count, and optional concise summary. A newly completed Artifact SHALL open automatically in an Adaptive Split unless the learner has collapsed auxiliary work for that turn. The split SHALL keep the current Lesson Kit page present; opening the canonical Paper page SHALL require an explicit native link. The action or Artifact SHALL NOT automatically navigate the current page.

#### Scenario: A managed Paper is handed off

- **WHEN** a valid Paper Artifact action resolves to a managed Paper in the current workspace
- **THEN** the conversation shows one card with the record's identity, title, and item count and offers Preview and explicit navigation

#### Scenario: Model claims disagree with the Paper record

- **WHEN** the action's model-supplied title or item count differs from the managed Paper record
- **THEN** the Artifact uses the managed record's title and item count

#### Scenario: Preview the latest Paper Artifact

- **WHEN** the learner previews the latest Artifact and has not collapsed auxiliary work for the current turn
- **THEN** its summary opens in a temporary Adaptive Split while the current Lesson Kit page remains visible

#### Scenario: A new Paper Artifact arrives

- **WHEN** a validated Paper Artifact is created during the current turn and the learner has not collapsed auxiliary work
- **THEN** its latest-result preview opens automatically without navigating away from the current Lesson Kit page

#### Scenario: Keep a live preview across reload

- **WHEN** the latest Artifact preview remains open after its turn completes and the learner reloads the same tab
- **THEN** that live preview is restored without changing the current Lesson Kit page

#### Scenario: Restore historical Artifact cards

- **WHEN** the learner opens a conversation containing earlier Paper Artifacts
- **THEN** their cards appear in the conversation history but do not reopen the Adaptive Split or navigate the current page

#### Scenario: Respect collapse for a later Artifact

- **WHEN** the learner has collapsed auxiliary work during the current turn and a Paper Artifact arrives
- **THEN** its card appears without automatically opening the split, and the learner can open it with Preview

#### Scenario: Repeated Artifact events in one conversation

- **WHEN** the same managed Paper Artifact is received more than once in one conversation
- **THEN** one card is rendered for that Paper in that conversation

#### Scenario: Use the native Paper destination

- **WHEN** the learner chooses to open a Paper Artifact
- **THEN** the link targets the current workspace's native saved-Paper page and ignores any model-provided URL
