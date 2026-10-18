## ADDED Requirements

### Requirement: Unaccepted and uncertain Agent messages remain recoverable
Before clearing the composer, the UI SHALL save outgoing text, captured request context, and a stable submission identity in browser storage. A definite request rejection SHALL remain visible and editable/retryable across reload. If acceptance is uncertain, the UI SHALL distinguish that state and reconcile by retrying the same identity and fields. Confirmed acceptance SHALL remove the saved local copy and display canonical conversation history. Recovery SHALL NOT overwrite a newer composer draft. A retry of an accepted failed turn SHALL be an explicit linked attempt; the UI SHALL NOT automatically replay a provider operation or its writes.

#### Scenario: The request is rejected
- **WHEN** the turn endpoint rejects a submission before acceptance
- **THEN** the original text remains recoverable after reload and retry does not replace a newer draft

#### Scenario: The acceptance response is lost
- **WHEN** the client cannot establish whether a request was accepted
- **THEN** the visible state says acceptance is uncertain and a retry uses the same identity and fields

#### Scenario: An accepted turn fails
- **WHEN** the provider fails and the conversation is reopened
- **THEN** the original message and failure status remain visible; any partial output is shown only when it exists

#### Scenario: Retry an accepted failure
- **WHEN** the learner explicitly retries a failed accepted turn
- **THEN** a new turn links to the original message and both turns remain in history

### Requirement: Provider activity cards show evidenced outcomes
The UI SHALL render normalized provider activities as semantic action cards with their actual status and outcome. Known impact SHALL come from normalized provider or backend evidence; unknown impact SHALL be identified as unknown. Diagnostics SHALL be folded and redacted, with a concise summary limited to 240 characters. The UI SHALL expose only backend-supported recovery controls and SHALL NOT present selective retry when no such operation exists. Existing approval behavior remains governed by its current capability contracts.

#### Scenario: A tool reports a result and an error
- **WHEN** normalized activity evidence contains a semantic action, terminal status, output, and diagnostic text
- **THEN** the card shows the action, actual status and evidenced result, while the redacted diagnostic stays folded

#### Scenario: Impact is not known
- **WHEN** an activity has no evidence of completed or failed effects
- **THEN** the card labels impact as unknown and does not infer success from a command string

#### Scenario: Selective recovery is unavailable
- **WHEN** a failed activity has no supported scoped retry operation
- **THEN** the UI offers no selective retry and may offer only an existing safe read-only or new-instruction affordance
