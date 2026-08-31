## MODIFIED Requirements

### Requirement: Minimal successful conversation mirror

Each workspace SHALL store conversations under `.lessonkit/jobs/conv-###/`. Lesson Kit
SHALL mirror provider session id, successful explicit user/assistant exchanges, context
anchors, concise change summaries, and the normalized Execution Plan activity records for
successful turns. It SHALL NOT mirror drafts, navigation events, hidden reasoning, failed
output, cancelled output, or raw provider protocol envelopes as durable conversation
history. Provider-native storage SHALL remain the complete context authority.

#### Scenario: Complete an explicit turn

- **WHEN** a provider turn completes successfully after running tools or commands
- **THEN** the explicit question, readable execution plan, final answer, context anchor,
  provider session id, and any change summary are available from the conversation endpoint

#### Scenario: Cancel a turn

- **WHEN** the learner cancels a running provider process
- **THEN** the turn reports cancelled and no cancelled partial output is appended to the
  successful transcript

## ADDED Requirements

### Requirement: Readable execution plan

The Bridge SHALL translate stable provider events into provider-neutral activity records
for command execution, tool calls, search, and answer generation. Each record SHALL carry a
human-readable label and a localized presentation state equivalent to running, completed,
or failed; updates for the same provider activity SHALL update one plan row rather than add
duplicate status lines. Command and tool details explicitly emitted by the provider MAY be
shown in a collapsible output area. Hidden reasoning SHALL NOT be shown, and raw provider
protocol event names SHALL NOT be used as learner-facing status text. Existing phase, text,
result, error, and done events SHALL remain readable for compatibility.

#### Scenario: Command progresses from start to completion

- **WHEN** a provider emits start and completion events for the same command item
- **THEN** the conversation shows one command row whose state changes from running to
  completed and whose emitted command output is available without overflowing the panel

#### Scenario: Provider streams its answer

- **WHEN** the provider emits answer text in multiple deltas
- **THEN** the deltas continue building one assistant answer bubble while the execution plan
  records answer generation as a readable step

#### Scenario: Unknown protocol phase is received

- **WHEN** a provider emits a protocol event for which no learner-facing activity exists
- **THEN** the event does not replace the status line with a raw protocol label

#### Scenario: Conversation is reopened

- **WHEN** a successful conversation containing command or tool activity is reopened
- **THEN** its coalesced execution plan is restored before the corresponding final answer
