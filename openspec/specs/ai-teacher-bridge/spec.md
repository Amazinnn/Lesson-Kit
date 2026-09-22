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

- **WHEN** the user runs `lesson-kit bridge add <provider> --command <cmd>`
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

- **WHEN** an agent runs `lesson-kit pull` and `lesson-kit record` to gather and record practice data
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

The bridge SHALL discover supported Agent CLIs from PATH. Codex, Claude, and Pi
SHALL be offered when their executables exist, with optional registry
configuration limited to command, arguments, model, and timeout. When the
registry configures an explicit command for a provider, that executable SHALL
take precedence over PATH discovery, so the resolved executable is never left
to PATH ordering alone. A conversation SHALL lock its selected provider. The
bridge SHALL NOT silently switch provider, create a replacement provider
session, or hide authentication, timeout, cancellation, nonzero-exit, or
provider-session-loss errors. A provider that reports a failure inside its own
event stream while still exiting zero SHALL be surfaced as a failed turn with
the provider's stated reason.

#### Scenario: Discover a local provider

- **WHEN** `codex`, `claude`, or `pi` is present on PATH
- **THEN** the providers endpoint lists it without requiring a duplicate command registration

#### Scenario: Explicit executable takes precedence over PATH

- **WHEN** the registry configures an explicit command for a provider whose name is also present on PATH
- **THEN** the provider is launched from the configured executable, and the providers listing reports that resolved path

#### Scenario: Provider fails during a turn

- **WHEN** the selected provider exits, times out, is cancelled, or cannot resume its native session
- **THEN** that turn reports the actual failure and the conversation remains locked to the same provider

#### Scenario: Provider reports failure inside its stream while exiting zero

- **WHEN** the provider process exits successfully but its event stream carries an error result
- **THEN** the turn is reported as failed with the provider's stated reason instead of as an answer-less success

### Requirement: Native session continuity

Codex conversations SHALL use stable exec/resume JSONL commands, Claude
conversations SHALL use print/resume stream-json commands, and Pi conversations
SHALL use print mode with JSON output plus native session resumption. The
provider SHALL run in the registered workspace, inherit local authentication,
configuration, skills, session store, and project instructions, and receive an
appended Lesson Kit teacher contract and server-rebuilt page context.

#### Scenario: Continue an existing provider session

- **WHEN** a learner sends a second turn in a conversation whose provider session id is known
- **THEN** the bridge invokes that provider's native resume command with the same session id

#### Scenario: Send a context-free learning question

- **WHEN** the learner asks a question while no practice problem is active
- **THEN** the provider still receives the fixed workspace/page context and can use `lesson-kit data` to search the pool

#### Scenario: Pi session id is taken from the provider's own header

- **WHEN** a Pi conversation completes its first turn
- **THEN** the native session id recorded for later resumption is the one the provider announced in its session header, not a server-generated identifier

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
- **THEN** the turn reports cancelled and no cancelled partial output is appended to the successful transcript

### Requirement: Serialized turn execution

A conversation SHALL run at most one provider turn at a time. Turn events SHALL have monotonically increasing sequence numbers for polling, and a temporary cancel operation SHALL target only the running turn.

#### Scenario: Send while a turn is running

- **WHEN** another turn is submitted to the same running conversation
- **THEN** the server rejects it as a conflict without queuing or writing a transcript entry

### Requirement: Readable execution plan

The Bridge SHALL translate stable provider events into provider-neutral
activity records. For Pi it SHALL emit only concrete command, file, search,
and tool activities; generic provider progress, hidden reasoning, and answer
generation SHALL not become learner-facing activity rows. Details and output
SHALL be sanitized before event storage, then bounded to 500 and 4000
characters respectively. Existing Codex and Claude activity behavior remains
compatible.

For Pi, read/view tools SHALL be labelled as file reads; write/edit/apply-patch
tools as file updates; grep/find/search tools as searches; bash/shell tools as
commands; and every concrete unmatched tool by its tool name. A shell command
that invokes `lesson-kit` or its module-form equivalent SHALL use the Lesson Kit
operation label instead of the generic command label.

#### Scenario: Pi reads a file

- **WHEN** Pi emits a read tool execution with a path
- **THEN** one activity identifies the file read and exposes no file contents in its summary

#### Scenario: Pi invokes Lesson Kit

- **WHEN** Pi runs `lesson-kit` or its module-form equivalent
- **THEN** the activity is labelled as a Lesson Kit operation and retains the sanitized command detail

#### Scenario: Pi updates a file

- **WHEN** Pi emits a write, edit, or apply-patch tool execution with a target path
- **THEN** one activity identifies the file update and its summary contains no written file body

#### Scenario: Pi searches

- **WHEN** Pi emits grep, find, or search with a bounded query
- **THEN** one activity identifies the search and retains only the sanitized query detail

#### Scenario: Pi calls another concrete tool

- **WHEN** Pi emits a tool execution outside the named read, write, search, and shell groups
- **THEN** one activity identifies that concrete tool by name without exposing raw protocol data

#### Scenario: Pi emits reasoning lifecycle

- **WHEN** Pi emits thinking start, delta, or end events
- **THEN** no reasoning content or generic reasoning activity is shown

#### Scenario: Successful conversation is reopened

- **WHEN** a successful Pi turn with concrete activities is reopened
- **THEN** its coalesced concrete activities are available with the final answer

#### Scenario: Command progresses from start to completion

- **WHEN** Codex or Claude emits start and completion events for the same command
- **THEN** the existing execution plan keeps one command row and updates its state

#### Scenario: Provider streams its answer

- **WHEN** a provider emits answer text in multiple deltas
- **THEN** contiguous deltas continue building readable assistant text

#### Scenario: Unknown protocol phase is received

- **WHEN** a provider emits a protocol event with no learner-facing activity
- **THEN** no raw protocol label replaces learner-facing status text

#### Scenario: Conversation is reopened

- **WHEN** a successful non-Pi conversation is reopened
- **THEN** its existing coalesced execution plan is restored before the answer

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

When a learner explicitly starts a goal-form assistance turn, the Agent MAY
return a `prefill_goal_form` action containing a title, goal kind, optional
start date, optional deadline, and description. The server SHALL accept this
action only under goal intent, validate its bounded field contract, and return
the cleaned fields for in-place form population. The action SHALL NOT create or
update the goal until the learner submits the form. Ordinary conversation SHALL
NOT populate goal fields.

#### Scenario: Agent supplies a goal period

- **WHEN** a goal-assistance response contains valid `start_date` and `deadline` values
- **THEN** both values populate the visible goal form and remain subject to learner confirmation

#### Scenario: One-line goal request fills the form

- **WHEN** the learner submits a one-line goal description from the goal form and the agent's reply carries a valid `prefill_goal_form` action
- **THEN** the form fields fill in place with a notice that the agent filled them, and nothing is saved until the learner submits

#### Scenario: Ordinary conversation cannot fill the form

- **WHEN** a turn without goal intent contains an action-like block
- **THEN** no goal-form action is applied

#### Scenario: No provider or no active conversation

- **WHEN** the goal-assist control is used with no provider configured or no active conversation
- **THEN** the UI states honestly what is missing and every manual goal feature keeps working

### Requirement: Check ingest action

The bridge SHALL parse a valid governed append-only content action without
depending on message keyword regexes and SHALL execute it automatically without
a confirmation dialog. A reply with no action SHALL perform zero content or
learning writes. Automatic actions MAY add knowledge points, formal problems,
micro quizzes, flash cards, and figures. Updating or deleting existing content,
rolling back a batch, and applying difficulty SHALL still require an explicit
learner instruction.

Large actions SHALL reference one complete manifest staged under the current
conversation's jobs directory. The server SHALL reject staged paths outside
that directory, impose no fixed six-item limit, validate the full manifest,
create a recoverable backup, and apply one atomic batch. Any invalid item SHALL
produce itemized errors and zero writes; the Agent SHALL repair and resubmit the
complete manifest rather than silently dropping items. Outcomes SHALL remain in
the mirror and next-turn context. Result cards SHALL show batch id, final asset
types/counts, workspace, backup, and current rollback state.

Provider file tools MAY read and write arbitrary local paths. Those external
tool writes are outside Lesson Kit's governed batch/rollback boundary. Managed
runtime, pool, staged-manifest, and figure destinations SHALL remain inside the
active workspace.

#### Scenario: Conversation request produces cards

- **WHEN** the Agent returns a valid append-only flash-card action
- **THEN** one governed batch inserts the cards automatically and restores a result card with rollback

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reopened after an action ran or was rolled back
- **THEN** the card reflects the current batch state and an already rolled-back batch has no rollback action

#### Scenario: Gate failure is explicit

- **WHEN** any item in the staged manifest fails validation
- **THEN** every reason is shown, the whole bundle writes nothing, and no success is claimed

#### Scenario: Ordinary conversation cannot ingest

- **WHEN** a provider returns ordinary answer text without a structured action
- **THEN** no content or learning row changes

#### Scenario: Malformed check action is explicit

- **WHEN** a provider returns malformed action JSON or an invalid staged-manifest reference
- **THEN** the conversation shows an explicit contract error and writes nothing

#### Scenario: Rejected manifest is correctable

- **WHEN** the Agent repairs the complete staged manifest from itemized errors
- **THEN** the full bundle is checked anew and may apply under one batch id

#### Scenario: Applied content is not resubmitted

- **WHEN** a prior action applied successfully and another turn starts
- **THEN** the provider receives the batch confirmation and avoids resubmitting the same content

#### Scenario: Examples carry the workspace course

- **WHEN** a content prompt is composed for an active course and chapter
- **THEN** all managed ids, staged paths, and destinations use that workspace scope

#### Scenario: Thirty items form one batch

- **WHEN** one valid staged bundle contains thirty requested problems
- **THEN** the complete list commits under one batch id instead of prompt-driven six-item turns

#### Scenario: Keyword-free follow-up

- **WHEN** the learner says `继续` and the Agent returns another valid append-only action
- **THEN** the action is processed without a keyword-derived intent boolean

### Requirement: Action block disclosure

A provider reply MAY carry multiple lessonkit-action blocks. The bridge SHALL
consider every block and apply the first one matching the active intent, not
only the first block in the reply. When a reply carries action blocks but none
is accepted, the bridge SHALL strip the blocks from the mirrored answer, record
that they were ignored with the reason, and carry that disclosure into the next
turn's provider context so the agent does not claim writes that never happened.
A block that matches an active intent but is discarded by its own field
contract (for example a goal form without a usable title) stays silently
discarded per that contract.

#### Scenario: A later matching block is not shadowed

- **WHEN** a reply under content-generation intent carries a practice-selection
  block followed by a bare flash-card manifest
- **THEN** the manifest is extracted and applied, and the earlier
  non-matching block does not shadow it

#### Scenario: Blocks without matching intent are disclosed

- **WHEN** a reply contains lessonkit-action blocks and no block matches the
  active intents
- **THEN** the blocks are removed from the mirrored answer, the turn records
  the ignored disclosure, nothing is written, and the next turn's provider
  context states that no write happened

### Requirement: Conversation mirror consistency during polling

The bridge SHALL keep conversation metadata, turn metadata, event streams, and
successful transcripts readable while an active provider turn updates them.
In-process readers and writers SHALL observe complete JSON values and complete
JSONL records; a polling read SHALL NOT cause a provider turn to fail because
the mirror file is being replaced.

#### Scenario: Poll while conversation metadata changes

- **WHEN** the browser polls a turn while the worker updates the conversation mirror
- **THEN** the poll reads either the prior or next complete value and the worker continues without a sharing violation

#### Scenario: Poll while an event is appended

- **WHEN** one thread appends the next sequenced event while another reads events
- **THEN** the reader receives only complete records with strictly increasing sequence numbers

### Requirement: Explicit Agent difficulty rating

An Agent MAY invoke difficulty check and apply only when the learner explicitly
asks to rate or rerate named problems. Ordinary conversation, content ingest,
and problem creation SHALL NOT trigger, queue, or suggest automatic rating.

#### Scenario: Explicit rating request

- **WHEN** the learner asks Pi to rate a bounded set of problems
- **THEN** Pi may check then apply one complete rating manifest through the CLI

#### Scenario: New content remains unrated

- **WHEN** an Agent creates a problem without a separate rating request
- **THEN** the content is ingested with all difficulty fields null

### Requirement: Conversation-owned Pi RPC process

The Bridge SHALL keep one `pi --mode rpc` process per active Pi conversation,
use strict LF-delimited JSONL, send correlated prompt/abort commands, and feed
streamed events into the existing normalized activity contract. The process
SHALL expire after 30 idle minutes; no separate simultaneous-process limit is
imposed. Conversation deletion and server shutdown SHALL close it, while a
later process resumes the saved native session.

One launch or handshake failure before prompt acceptance MAY restart once. A
crash after acceptance SHALL fail the turn without replaying the prompt because
tools may already have caused side effects. Cancellation SHALL send RPC abort
before terminate/kill fallback. All provider child processes SHALL launch
without a visible Windows console.

#### Scenario: Several turns reuse one process

- **WHEN** three serialized turns run in one active Pi conversation
- **THEN** one Pi PID handles all three and native context continues

#### Scenario: Resume after idle expiry

- **WHEN** a Pi process expires after 30 idle minutes and a new turn arrives
- **THEN** a hidden RPC process resumes the saved native session

#### Scenario: Handshake fails once

- **WHEN** Pi fails before accepting the prompt on the first launch
- **THEN** the Bridge restarts once and sends the prompt only after a successful handshake

#### Scenario: Process dies after acceptance

- **WHEN** Pi exits after accepting a prompt and possibly running tools
- **THEN** the turn fails with preserved events and the prompt is not automatically replayed

#### Scenario: Cancel an RPC turn

- **WHEN** the learner stops an active Pi turn
- **THEN** the Bridge sends abort, mirrors no successful exchange, and kills only if abort fails

#### Scenario: Windows providers stay hidden

- **WHEN** any configured provider process starts on Windows
- **THEN** no terminal window becomes visible

