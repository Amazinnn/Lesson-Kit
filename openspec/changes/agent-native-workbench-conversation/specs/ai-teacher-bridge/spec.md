## ADDED Requirements

### Requirement: Provider-native conversation discovery

The bridge SHALL discover supported Agent CLIs from PATH. Codex and Claude SHALL be offered when their executables exist, with optional registry configuration limited to arguments, model, and timeout. A conversation SHALL lock its selected provider. The bridge SHALL NOT silently switch provider, create a replacement provider session, or hide authentication, timeout, cancellation, nonzero-exit, or provider-session-loss errors.

#### Scenario: Discover a local provider

- **WHEN** `codex` or `claude` is present on PATH
- **THEN** the providers endpoint lists it without requiring a duplicate command registration

#### Scenario: Provider fails during a turn

- **WHEN** the selected provider exits, times out, is cancelled, or cannot resume its native session
- **THEN** that turn reports the actual failure and the conversation remains locked to the same provider

### Requirement: Native session continuity

Codex conversations SHALL use stable exec/resume JSONL commands and Claude conversations SHALL use print/resume stream-json commands. The provider SHALL run in the registered workspace, inherit local authentication, configuration, skills, session store, and project instructions, and receive an appended Lesson Kit teacher contract and server-rebuilt page context.

#### Scenario: Continue an existing provider session

- **WHEN** a learner sends a second turn in a conversation whose provider session id is known
- **THEN** the bridge invokes that provider's native resume command with the same session id

#### Scenario: Send a context-free learning question

- **WHEN** the learner sends a question while no practice problem is active
- **THEN** the provider still receives the fixed workspace/page context and can use `wb data` to search the pool

### Requirement: Minimal successful conversation mirror

Each workspace SHALL store conversations under `.lessonkit/jobs/conv-###/`. Lesson Kit SHALL mirror provider session id, successful explicit user/assistant exchanges, context anchors, and concise change summaries. It SHALL NOT mirror drafts, navigation events, raw provider tool logs, failed output, or cancelled output as durable conversation history. Provider-native storage SHALL remain the complete context authority.

#### Scenario: Complete an explicit turn

- **WHEN** a provider turn completes successfully
- **THEN** the explicit question, final answer, context anchor, provider session id, and any change summary are available from the conversation endpoint

#### Scenario: Cancel a turn

- **WHEN** the learner cancels a running provider process
- **THEN** the turn reports cancelled and no cancelled partial output is appended to the successful transcript

### Requirement: Serialized turn execution

A conversation SHALL run at most one provider turn at a time. Turn events SHALL have monotonically increasing sequence numbers for polling, and a temporary cancel operation SHALL target only the running turn.

#### Scenario: Send while a turn is running

- **WHEN** another turn is submitted to the same running conversation
- **THEN** the server rejects it as a conflict without queuing or writing a transcript entry
