## Purpose

The AI teacher bridge connects the workbench to an external agent CLI without
embedding an AI kernel: tasks carry an output contract, run asynchronously, and
are validated before their results are trusted.
## Requirements
### Requirement: Provider configuration

The bridge SHALL read provider definitions (command, arguments, working
directory mode, timeout) from a config file, and the workbench SHALL expose
provider configuration as a CLI operation. Configured values serve as
conversation-provider overrides (arguments, model, timeout) for the locally
discovered agent CLIs.

#### Scenario: Configure a provider

- **WHEN** the user runs `wb bridge add <provider> --command <cmd>`
- **THEN** the provider is written to the bridge config and applies to
  conversations that use that provider

### Requirement: Workbench operates without AI

The workbench SHALL be fully functional with no provider configured and no AI
conversation ever started: registry, weak list, pull, practice, feedback, and
scheduling SHALL work identically with or without the bridge.

#### Scenario: Practice without any provider

- **WHEN** no bridge provider is configured and the learner practices problems
- **THEN** every non-AI feature works unchanged and AI conversations are shown as unavailable rather than broken

### Requirement: CLI is a data interface, not a teacher

The super CLI SHALL expose only data operations — query pool content, pull
problems, record attempts and feedback, read workspace state — and SHALL carry
no teaching semantics. Teaching behavior (how to teach, when to ask, how to
close a topic) SHALL live in the teaching layer (skills and teaching
contracts), never in the CLI. The same teaching capability SHALL be reachable
through the web shell, whose AI panel is a thin conversation surface over the
same bridge conversations.

#### Scenario: CLI records data without pedagogy

- **WHEN** an agent runs `wb pull` and `wb record` to gather and record practice data
- **THEN** the CLI returns and stores data only, with no teaching instructions, and the agent's teaching behavior comes from the teaching skill it loaded

### Requirement: Flexible session model

A teaching session SHALL NOT be bound to a single task or a fixed flow: the
agent SHALL freely use data interfaces to explore problems and materials for
the conversation, the learner SHALL be able to start a new session at any time,
and sessions SHALL be recorded as trace artifacts (anchor, exchanges, outcomes)
rather than enforced as state machines. Process control SHALL follow layered
adaptation: macro (session purpose anchored to pool items), meso (session
lifecycle, learner-controlled), micro (turn-level conduct in the teacher
contract). Anti-derailment SHALL work through anchoring, parking digressions,
and learner control — never through hard-coded pedagogical transitions.
Session traces SHALL include the learner's own answers given during the
conversation (DeepTutor-style trace), so conversation answers become recorded
learning data that can feed signals and later memory features.

#### Scenario: A session changes topics freely

- **WHEN** a conversation drifts toward a related but unplanned question
- **THEN** the agent parks the digression visibly, returns to the session anchor, and the learner can open a new session for the digression at any time

#### Scenario: Session trace is recorded

- **WHEN** a teaching session ends
- **THEN** a trace artifact records the anchor, the exchanges including the learner's answers, and the outcomes under the session's job area, without locking any future session to it

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

### Requirement: Explicit practice action

The Bridge MAY mirror a structured `replace_practice_selection` action only when
the request carries explicit practice intent. The action SHALL contain a
non-empty list of existing knowledge-point ids and SHALL be ignored for ordinary
conversation.

#### Scenario: Ordinary conversation
- **WHEN** a turn contains no explicit practice intent
- **THEN** any action-like text cannot change browser selection

#### Scenario: Explicit replacement
- **WHEN** a turn contains practice intent and valid knowledge-point ids
- **THEN** the client replaces the current selection exactly once

### Requirement: Goal-form assist action

The bridge MAY mirror a second structured action, `prefill_goal_form`, only
when the request carries explicit goal intent (a goal-assist request from the
goal form). The action SHALL carry at most the fields title, kind, deadline,
and description, validated server-side against the goal contract; invalid or
missing fields SHALL be dropped, and an action without a usable title SHALL
be discarded entirely. The client SHALL apply the action in place by filling
the goal form — submission remains an explicit human action. Ordinary
conversation SHALL NOT fill the goal form, and no goal is ever created or
modified by the action itself.

#### Scenario: One-line goal request fills the form

- **WHEN** the learner submits a one-line goal description from the goal form
  and the agent's reply carries a valid `prefill_goal_form` action
- **THEN** the form fields fill in place with a notice that the agent filled
  them, and nothing is saved until the learner submits

#### Scenario: Ordinary conversation cannot fill the form

- **WHEN** a turn without goal intent contains an action-like block
- **THEN** no goal-form action is applied

#### Scenario: No provider or no active conversation

- **WHEN** the goal-assist control is used with no provider configured or no
  active conversation
- **THEN** the UI states honestly what is missing and every manual goal
  feature keeps working

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
surfaced as an explicit error rather than silently dropped.

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

