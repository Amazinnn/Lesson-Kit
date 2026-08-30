## MODIFIED Requirements

### Requirement: Check ingest action

The bridge MAY mirror a third structured action, `check_ingest`, only when the
request carries explicit content-generation intent (the learner asks the agent
to produce or add pool content). The action SHALL carry an inline manifest of
kind `flash-card-patch` or `micro-quiz-patch`; the server SHALL validate it
through the same deterministic gates as the CLI recipes and, on pass, apply it
as one batch-recorded transactional apply. Gate failures SHALL be reported
back into the conversation flow item by item and SHALL write nothing. Success
SHALL be presented as an independent result card in the conversation flow
showing the batch id, kind, item counts, and backup path, with a rollback
affordance that calls the same whole-batch rollback as the CLI. The
conversation mirror SHALL carry the check ingest action and its outcome so
the result card is restored when the conversation is re-rendered. Ordinary
conversation without content-generation intent SHALL NOT trigger the action,
and a malformed `check_ingest` block under content-generation intent SHALL be
surfaced as an explicit error rather than silently dropped. When a new turn
starts in a conversation whose previous turn carried a check ingest action,
the server-side provider context SHALL carry that action's outcome — a batch
confirmation on success, or the itemized rejection reasons on failure — so
the agent can correct a rejected manifest or avoid resubmitting applied
content.

#### Scenario: Conversation request produces cards

- **WHEN** the learner asks the agent in conversation to add flash cards for a
  knowledge point and the reply carries a valid `check_ingest` action
- **THEN** the manifest passes the deterministic gate, one batch-recorded
  apply inserts the cards, and an independent result card with the batch id
  and a rollback affordance appears in the conversation flow

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reloaded after a check ingest action ran
- **THEN** the mirrored assistant message carries the action outcome and the
  result card is restored in the conversation flow

#### Scenario: Gate failure is explicit

- **WHEN** the action's manifest fails the deterministic gate
- **THEN** the conversation flow lists every rejection reason, nothing is
  written to the pool, and no result card claims success

#### Scenario: Ordinary conversation cannot ingest

- **WHEN** a turn without content-generation intent contains an action-like
  block
- **THEN** no check ingest action runs

#### Scenario: Malformed check action is explicit

- **WHEN** a turn with content-generation intent carries a `check_ingest`
  block that is not valid JSON or does not satisfy the manifest structure
- **THEN** the conversation flow shows an explicit error for the block instead
  of silently dropping it

#### Scenario: Rejected manifest is correctable

- **WHEN** a previous turn's check ingest action was rejected and the next
  turn asks the agent to fix and resubmit
- **THEN** the provider context carries the itemized rejection reasons and a
  corrected manifest is gated and applied anew

#### Scenario: Applied content is not resubmitted

- **WHEN** a previous turn's check ingest action applied successfully and a
  new turn starts
- **THEN** the provider context carries the batch confirmation so the agent
  does not resubmit the same content
