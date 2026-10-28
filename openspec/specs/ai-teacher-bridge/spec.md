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

### Requirement: Agent context follows current learning state

The Bridge SHALL rebuild learning context from managed Lesson Kit state rather
than requiring the learner to repeat material already visible in the workbench.
Browser payloads MAY identify the current page, selection, filter, focused
object, and unsent draft, but durable facts SHALL be read back from the active
practice, saved practice sets, attempts, and Pool rows on the server.

Practice context SHALL use the workspace's active-practice progress and ordered
items as the progress authority. The browser's current selection and filter
values SHALL be bounded supplemental focus only. The saved-paper page SHALL
expose bounded paper summaries and, when one paper is focused, its managed
problem content. The records page SHALL expose a bounded recent attempt view.
Knowledge-point selections SHALL resolve to existing Pool objects before they
reach the provider. These reads SHALL NOT themselves create attempts, ratings,
papers, practices, or other learning writes.

#### Scenario: Discuss the current practice without copying it

- **WHEN** the learner asks about a practice problem or unfinished practice visible in the workbench
- **THEN** the provider receives the durable active-practice progress and current Pool problem context without requiring the learner to paste the question

#### Scenario: Discuss the current Paper assembly focus

- **WHEN** the learner is choosing knowledge-point scope, source filters, or years for Paper assembly
- **THEN** the provider receives a bounded representation of that assembly-focus context while the Pool remains the authority for resolved learning objects

#### Scenario: Discuss a saved paper

- **WHEN** the learner asks about the 组卷 page or focuses one saved paper
- **THEN** the provider receives bounded managed paper summaries and the focused paper's ordered problem context when available

#### Scenario: Discuss recent practice records

- **WHEN** the learner asks about the 做题记录 page
- **THEN** the provider receives a bounded recent durable attempt view including recorded status and available verdict/rating information

#### Scenario: Reading visible state is not a write

- **WHEN** any of these contexts is attached to an ordinary Agent turn
- **THEN** no attempt, rating, active practice, or saved paper is created or modified merely because the context was read

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

A conversation SHALL run at most one provider turn at a time. A new message accepted with the queue action during an active turn SHALL be retained with its submission-time context, appended by default in FIFO order. Explicit accepted reorder operations SHALL define the shared persisted display and dispatch order. Interrupt-and-send SHALL use a separate stop-and-handoff path and SHALL NOT enter the ordinary queue. Successful or failed ordinary turns SHALL allow the next queued message to run after worker release without relying on an open browser tab, provided the queue was not already paused. The failed turn itself SHALL NOT be automatically retried. A failure to launch the worker itself SHALL retain the existing pause-and-manual-continue behavior. A cancelled turn without an interrupt intent or an unexpectedly interrupted turn SHALL pause retained messages until explicit continuation. Service recovery SHALL report an unowned running turn as interrupted or failed and pause all retained work without dispatching it. A progress-read failure alone SHALL NOT change turn or queue status. Turn events SHALL have monotonically increasing sequence numbers, and cancellation SHALL target the captured running turn.

#### Scenario: Send while a turn is running

- **WHEN** turn A is running and messages B and C are accepted with the queue action
- **THEN** B and C remain visible in default FIFO order with their captured contexts, and neither provider starts before A reaches a terminal status

#### Scenario: Continue ordinary work after success

- **WHEN** A completes successfully while B and C are queued and the queue is not paused
- **THEN** B starts after A's provider worker has returned, and C starts after B succeeds without requiring browser polling or navigation

#### Scenario: Failure does not block later messages

- **WHEN** A fails while B and C are queued and the queue was not already paused
- **THEN** B and C continue in order after worker release, while A requires a manual retry

#### Scenario: Cancellation pauses later messages

- **WHEN** A is cancelled without an accepted interrupt message while B and C are queued
- **THEN** B and C remain accepted and paused until the learner explicitly continues the queue

#### Scenario: Pause survives service recovery

- **WHEN** the service reads a conversation containing an unowned running turn and queued messages
- **THEN** it marks the running turn interrupted or failed, retains the messages, and leaves dispatch paused

#### Scenario: Progress cannot be read

- **WHEN** a progress request fails while the provider turn has no authoritative terminal status
- **THEN** the turn remains active and no later provider turn starts

#### Scenario: Dispatch after an explicit reorder

- **WHEN** A completes and the confirmed queued order has been changed from B/C to C/B
- **THEN** C starts after A releases provider ownership, then B may start after C succeeds; browser polling is not required

#### Scenario: Legacy conversation order

- **WHEN** a conversation has queued turns but no explicit queue-order field
- **THEN** reads preserve the existing numeric-turn FIFO order without rewriting unrelated artifacts; a later accepted queue mutation persists the explicit order

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
conversation's jobs directory. An inline manifest SHALL be accepted whether it
declares its `kind` or its `type` as `content-bundle`. The server SHALL reject
staged paths outside that directory, impose no fixed item ceiling, validate the
full manifest, create a recoverable backup, and apply one transaction. One
manifest MAY span several chapters: every knowledge point, problem, and flash
card SHALL resolve exactly one chapter (its own `chapter`, else the manifest's), a
manifest that leaves any item without a chapter SHALL be refused with that item's
label instead of falling back to the workspace chapter, and every derived value —
allocated id prefix, figure destination, micro-quiz id, duplicate check — SHALL
follow the item's chapter. The apply SHALL record one batch per chapter present,
so a chapter can be rolled back on its own, while prevalidation, backup, and the
transaction cover the whole manifest. Every content action block in one reply
SHALL be applied in order, so a learner who asks for several chapters is served
in one turn. Any invalid item SHALL produce itemized errors and zero writes; the
Agent SHALL repair and resubmit the complete manifest rather than silently
dropping items. Outcomes SHALL remain in the mirror and next-turn context, where
a successful apply SHALL also tell the Agent to continue any chapters the learner
asked for that are still missing rather than asking the learner for another
「继续」. Result cards SHALL show batch id, final asset types/counts, workspace,
backup, and current rollback state.

Provider file tools MAY read and write arbitrary local paths. Those external
tool writes are outside Lesson Kit's governed batch/rollback boundary. Managed
runtime, pool, staged-manifest, and figure destinations SHALL remain inside the
active workspace.

#### Scenario: Conversation request produces cards

- **WHEN** the Agent returns a valid append-only flash-card action
- **THEN** one governed batch inserts the cards automatically and restores a result card with rollback

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reopened after an action ran or was rolled back
- **THEN** the card reflects the current batch state and an already rolled-back batch has no rollback action, and a turn carrying one action renders one card

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

#### Scenario: Every content action of one reply is applied

- **WHEN** a reply carries one content action for chapter 12 and another for chapter 13
- **THEN** both are applied in order, each with its own batches, and both results stay in the mirror

#### Scenario: One failing action leaves the others alone

- **WHEN** a reply carries two content actions and the second fails validation
- **THEN** the first is applied and recorded, the second writes nothing, and its itemized reasons reach the learner and the next turn

#### Scenario: A multi-chapter bundle reports each batch

- **WHEN** an applied bundle contains content for two chapters
- **THEN** the result lists both batches with their chapters and counts, and each card row offers its own rollback

#### Scenario: One reply imports several chapters

- **WHEN** a learner asks for three chapters and the Agent answers with one manifest spanning them, or with one content block per chapter
- **THEN** every chapter is written in that turn, one batch per chapter, and no further learner message is required to finish the request

#### Scenario: An inline manifest is accepted

- **WHEN** a reply carries a small inline manifest whose block declares `type` as `content-bundle`
- **THEN** the manifest is applied exactly as the staged form, with no contract error

#### Scenario: A chapter-less item is refused with its label

- **WHEN** a manifest has no bundle-level chapter and an item declares none, even though the workspace has an active chapter
- **THEN** that item is refused with its label and a reason that names the missing chapter, and nothing is written

#### Scenario: Stopping early is corrected next turn

- **WHEN** an import applied successfully for some of the chapters the learner asked for
- **THEN** the next-turn context states the applied batches and tells the Agent to continue the remaining chapters without waiting for another learner message

### Requirement: Action block disclosure

A provider reply MAY carry multiple lessonkit-action blocks. The bridge SHALL
consider every block: every content block SHALL be applied, and an
intent-gated block SHALL be applied only for its active intent. Applying several
content blocks SHALL NOT be treated as a conflict. When a reply carries action
blocks but none is accepted, the bridge SHALL strip the blocks from the mirrored
answer, record that they were ignored with the reason, and carry that disclosure
into the next turn's provider context so the agent does not claim writes that
never happened.
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

#### Scenario: Several content blocks all land

- **WHEN** a reply carries three content manifests, one per chapter
- **THEN** all three are applied in the order they appear and none is dropped silently

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

### Requirement: Agent CLI calls preserve error feedback

The Agent prompt SHALL give the correct workspace-aware CLI argument order and
direct the Agent to query the relevant subcommand help when uncertain. Lesson
Kit invocations SHALL be issued independently without output pipelines,
failure-suppressing fallbacks, or trailing commands masking their exit status.
The Bridge SHALL use provider-reported activity outcomes rather than classify
failure by matching words in output. A failed tool call MAY be followed by a
corrected invocation without automatically failing the whole conversation.

#### Scenario: Invalid CLI arguments

- **WHEN** an independent CLI invocation omits a required workspace or supplies unknown arguments
- **THEN** it returns nonzero with diagnostic output and a provider-reported error is retained as a failed activity

#### Scenario: Successful output mentions error

- **WHEN** a provider reports success and its output contains the word error
- **THEN** the Bridge does not override success based on that text

#### Scenario: Corrected invocation succeeds

- **WHEN** the Agent corrects a failed invocation and issues a new successful call
- **THEN** both activities retain their own outcomes and the Agent reports success only from the successful result

### Requirement: Learner-requested Agent attempt recording

The Agent MAY inspect accessible workspace material and use the public
`lesson-kit attempts` CLI to record or correct a problem attempt when the
learner requests that action. The Agent SHALL receive the focused practice
context and the CLI's structured result. Reading a page, a draft, an image, or
an existing attempt SHALL NOT itself write a learning record. The Bridge SHALL
NOT silently turn an ordinary conversation into an attempt or rating.

#### Scenario: Discuss a draft without recording

- **WHEN** the learner asks about the current solution without asking to record or grade it
- **THEN** the Agent can read the focused content but no attempt or feedback is added

#### Scenario: Record a photographed solution

- **WHEN** the learner asks the Agent to transcribe and grade local answer images
- **THEN** the Agent may read them with existing file tools and submit one checked attempt manifest through the CLI

### Requirement: Provider turn budgets follow progress

A provider turn budget SHALL measure silence rather than total duration: every
provider record or output line SHALL reset it, and while a command or tool call
is in flight the longer tool budget SHALL apply, so a slow command is never cut
off mid-run. A turn that produces no record for the applicable budget SHALL fail
as a provider timeout through the existing failure path. The tool budget SHALL be
at least the silence budget and remain shorter than the idle process window, so a
stuck turn fails with its own reason before its provider process is recycled.
Both budgets SHALL be configurable per provider, and the default silence budget
SHALL NOT be shorter than the one already in force.

#### Scenario: A long answer is not a timeout

- **WHEN** a provider keeps reporting events for longer than the silence budget
- **THEN** the turn keeps running and is never failed as a timeout for taking a long time

#### Scenario: A slow command is not cut off

- **WHEN** a command or tool call runs without output for longer than the silence budget
- **THEN** the turn keeps running for at least the tool budget and the command is allowed to finish

#### Scenario: Real silence is still a stall

- **WHEN** nothing arrives for the silence budget while no command is in flight
- **THEN** the turn fails as a provider timeout, the process is stopped, and no transcript entry is written

#### Scenario: The budgets are visible and configurable

- **WHEN** a provider is configured or listed
- **THEN** both its silence budget and its tool budget are readable, and the tool budget is below the process idle window

### Requirement: Explicit in-place problem edit action

The bridge SHALL accept one more governed manifest shape, `problem-patch`, whose
items name existing problems and the attributes to change, and SHALL apply it
through the same prevalidation, backup, transaction, batch id, and
previous-value snapshot as the other content actions. It SHALL be treated as an
edit rather than an append: the bridge SHALL execute it only when the learner
explicitly asks to change existing content, and never because a conversation
merely discussed a change. The next-turn context SHALL report the applied patch
batch and its counts, including how many difficulty ratings the patch cleared,
and the contract SHALL tell the Agent that an in-place patch preserves the id and
every learning record, that a patch batch can be rolled back value for value, and
that options may be lifted verbatim out of a problem's old text instead of
re-importing the problem.

#### Scenario: An explicitly requested conversion runs

- **WHEN** the learner asks to turn named problems into 判断/小测 items and the Agent returns a valid `problem-patch` manifest
- **THEN** those rows change in place under one batch id, and the Agent's next turn sees the batch and counts

#### Scenario: A patch is not automatic

- **WHEN** a reply carries a `problem-patch` manifest that the learner did not ask for
- **THEN** the content boundary's explicit-instruction rule still governs, and ordinary conversation never edits existing content

#### Scenario: The Agent is told what a patch preserves

- **WHEN** a content prompt is composed for an active workspace
- **THEN** it states that in-place patching keeps the problem id and learning records, that the batch can be rolled back, and that splitting options out of an old stem is preferred over deleting and re-importing

### Requirement: Per-harness model catalog

The Bridge SHALL discover Agent harnesses independently from the models available
inside each harness. A conversation SHALL choose exactly one harness at creation,
and model enumeration SHALL never make that conversation selectable as another
harness.

Configured named entries SHALL preserve their display name, model id, harness,
and optional extra arguments. Each available harness SHALL expose a model list
through one bridge contract:

- Codex SHALL query its supported app-server `model/list` RPC and MAY fall back
  to its local model cache when runtime discovery is unavailable.
- Claude Code SHALL expose its supported model catalog plus configured named
  entries.
- Pi SHALL augment configured targets with models reported by
  `get_available_models`.

Discovery failure SHALL degrade to configured/default targets for that harness,
not remove unrelated harnesses or make Agent chat unavailable.

#### Scenario: Codex runtime models are enumerated

- **WHEN** Codex app-server returns picker-visible models
- **THEN** the Codex harness exposes those models without requiring duplicate Lesson Kit configuration

#### Scenario: Claude model choices stay in Claude

- **WHEN** Claude Code is discovered
- **THEN** its supported Claude model choices are exposed under the Claude harness only

#### Scenario: Pi runtime models appear without manual duplication

- **WHEN** Pi reports configured models through `get_available_models`
- **THEN** models not already represented by configured Pi entries are added as Pi runtime choices

#### Scenario: Runtime discovery is best effort

- **WHEN** a harness-specific model discovery mechanism cannot answer
- **THEN** that harness retains its configured/default target and other harnesses are unaffected

### Requirement: Conversation harness is immutable

A Lesson Kit conversation SHALL record the harness selected at creation together
with its current model, configured entry identity, and entry-specific arguments.
Existing conversation records that contain only `provider` and `model` SHALL
remain readable.

The harness SHALL be immutable for the lifetime of the conversation. An attempt
to PATCH or otherwise switch a conversation to a different harness SHALL be
rejected and SHALL NOT alter its native session pointer, transcript, or local
conversation id. A learner who wants another harness SHALL create another
conversation.

The in-chat selector SHALL offer only models belonging to the conversation's
harness. Same-harness switching SHALL be refused while a turn is running and
SHALL take effect on the next turn. Codex and Claude MAY resume the same native
session with the newly selected model. For an active Pi RPC process, a
provider-qualified model switch SHALL use Pi's native `set_model` RPC first;
if live switching is unavailable, the process MAY be recycled while the same
conversation/harness binding remains.

#### Scenario: Named entry arguments survive selection

- **WHEN** a configured model entry carries extra launch arguments
- **THEN** the conversation stores and applies those arguments on every turn

#### Scenario: Pi switches the live process

- **WHEN** an idle Pi conversation has a live RPC process and the learner selects another provider-qualified Pi model
- **THEN** the Bridge calls `set_model` and keeps that process when Pi accepts the switch

### Requirement: Managed Paper Artifact actions resolve to saved Paper records

The on-demand `actions` contract SHALL instruct the Agent to emit a `paper_artifact` presentation action only after it has run `lesson-kit papers <workspace> save --input <manifest>` and observed exit code 0 with a JSON receipt. For a received action, the Workbench SHALL validate a syntactically valid `ps-NNN` id in the selected workspace and resolve it against that workspace's existing managed Paper record. The normalized action's identity, title, and item count SHALL come from that record; model-supplied title or count SHALL NOT override it. The action block is not a receipt ledger and does not by itself prove which command produced the id. An optional summary SHALL be limited to 300 characters and treated as presentation text, not proof of a save. A model-provided URL SHALL be discarded, and the normalized action SHALL contain no navigation URL. An invalid id or missing managed record SHALL produce no Artifact action and SHALL NOT write learning or Paper data.

#### Scenario: Agent follows the managed-save instruction

- **WHEN** the Agent receives exit code 0 and a JSON receipt from the managed Paper save command
- **THEN** its action contract directs it to emit `paper_artifact` with the Paper id from that receipt and no navigation URL

#### Scenario: Resolve the selected workspace record

- **WHEN** the Workbench receives a syntactically valid Paper id with a matching record in the selected workspace
- **THEN** the normalized action contains the managed record's id, title, and item count, plus the optional summary, and contains no URL

#### Scenario: Ignore model-only identity claims

- **WHEN** the action supplies a title or item count that differs from the matching managed Paper record
- **THEN** the normalized action uses the managed record's title and item count

#### Scenario: Reject an unmanaged or malformed Paper id

- **WHEN** the action id is malformed or no matching managed Paper record exists in the selected workspace
- **THEN** no Paper Artifact action is returned and no record is created

#### Scenario: Do not treat an export as a saved Paper

- **WHEN** the learner requested only a `pull --plan` manifest or `pull --print` sheet and no successful managed save receipt exists
- **THEN** the Agent's action contract directs it to emit no Paper Artifact action

#### Scenario: Discard a model-provided destination

- **WHEN** a `paper_artifact` block includes a URL
- **THEN** the URL is removed from the normalized action and cannot control navigation

### Requirement: Accepted Agent messages survive failed turns

When a turn request includes a `submission_id`, the bridge SHALL persist the originally accepted user text, the current user text, the original captured context, and stable task fields in the existing turn artifact before provider dispatch. Repeating that identity with the same originally submitted text and task fields SHALL return the same turn without changing its current text, queue position, context, or dispatch state. Reusing the identity with changed task fields SHALL return a conflict. Delivery action is routing metadata and SHALL NOT change the submitted task identity. Editing a queued message SHALL change only its current text and queue revision; it SHALL preserve the original identity and context. An explicit retry of a failed edited message SHALL use its current text and original captured context. Requests without `submission_id` SHALL retain their existing behavior.

Conversation history SHALL include accepted turn messages independently of successful transcript exchanges. A turn already represented by a legacy successful transcript SHALL appear exactly once. Failed turns SHALL expose only actual public partial output and their truthful terminal status; history SHALL NOT invent missing user text, assistant output, or legacy failures.

#### Scenario: Provider fails after acceptance

- **WHEN** the provider fails before producing an answer for an accepted turn
- **THEN** reopening history shows the original accepted user text and failed status, with any actual public partial output

#### Scenario: Acceptance response is lost and retried

- **WHEN** the client repeats the same `submission_id` and submitted task fields after an unknown response
- **THEN** the bridge returns the original turn without dispatching a second provider, even if that pending message has since been edited

#### Scenario: Same identity is reused with changed fields

- **WHEN** a request reuses a stored `submission_id` with different text as originally accepted or different submitted task fields
- **THEN** the bridge returns a conflict and leaves the accepted turn unchanged

#### Scenario: Delivery action changes before retry

- **WHEN** the same accepted submission is reconciled with a different queue or interrupt action
- **THEN** the bridge returns the original turn and does not change its existing routing or execution state

#### Scenario: Retry an edited failed message

- **WHEN** a queued message is edited, later fails after execution, and the learner explicitly retries it
- **THEN** the new linked turn uses the edited text and the original captured context

#### Scenario: Server enrichment changes before duplicate resolution

- **WHEN** the same submitted task fields are retried after server-derived page enrichment has changed
- **THEN** the bridge returns the original turn and retains its originally captured context

#### Scenario: Read legacy successful history

- **WHEN** a conversation contains successful transcript exchanges created before this change
- **THEN** each exchange remains readable once and no missing failed-message text is synthesized

### Requirement: Interrupt-and-send waits for the old turn to stop

An explicit interrupt-and-send SHALL durably accept its message and bind its cancellation request to the running turn that was current at acceptance. It SHALL start the interrupt message directly only after that captured turn's provider worker reaches an authoritative terminal state and releases ownership. The interrupt SHALL NOT be inserted into the ordinary queue, depend on queue continuation, or fall back to queue routing; waiting for stop confirmation is an independent handoff state. A stop request, timeout, or missing progress response alone SHALL NOT authorize concurrent execution. The bridge SHALL preserve already completed effects and SHALL NOT resume or roll back the old task automatically. Messages queued before the interrupt SHALL remain paused after the interrupt message, including when it succeeds. While an interrupt message is waiting for stop confirmation, another distinct interrupt submission SHALL be rejected as a conflict without discarding the accepted one.

#### Scenario: Interrupt A with queued B/C and send D

- **WHEN** A is running, B and C are queued, and D is accepted with interrupt-and-send
- **THEN** D waits for A's actual terminal acknowledgement, then runs once, while B and C remain retained and paused after D

#### Scenario: A finishes as cancellation races

- **WHEN** D is accepted while A is running but A reaches a normal terminal result before its cancellation takes effect
- **THEN** D still runs after A, and B and C remain paused

#### Scenario: Stop acknowledgement is unavailable

- **WHEN** A has not reached an authoritative terminal state after D requests cancellation
- **THEN** D remains visibly waiting for stop confirmation and no second provider runs

#### Scenario: A second interrupt is submitted

- **WHEN** a distinct interrupt message is submitted while an earlier interrupt message is waiting for A to stop
- **THEN** the new submission receives a conflict and the earlier accepted interrupt message remains intact

#### Scenario: Interrupt when no queue exists

- **WHEN** A runs, no queued messages exist, and D is accepted with interrupt-and-send
- **THEN** cancellation targets A and D runs directly after A is authoritatively terminal and releases ownership; no ordinary queue is created or resumed

#### Scenario: Interrupt when no provider is running

- **WHEN** D is submitted with interrupt-and-send while no provider owns the conversation and no approval or other handoff blocks acceptance
- **THEN** D starts directly without an artificial queue step or explicit continue action, and any pre-existing paused queued messages remain paused

#### Scenario: Approval blocks interrupt acceptance

- **WHEN** a new interrupt message is submitted while a Paper approval is pending
- **THEN** the service rejects it with a conflict before accepting or enqueuing it, and no provider or Paper operation runs

#### Scenario: Service restarts during an interrupt handoff

- **WHEN** the service restarts before an accepted interrupt message begins and cannot safely complete the captured old-worker handoff
- **THEN** it retains the accepted message as interrupted or failed for explicit recovery, does not convert it to queued work, does not run it automatically, and keeps any ordinary queued messages paused

### Requirement: Pending messages can be revised or removed before execution

A pending message SHALL retain its current text and captured context in its accepted turn artifact. The learner MAY edit or remove it only while it has not begun provider execution. Each successful edit SHALL increment that message's revision; edit and removal requests SHALL include the expected revision and SHALL conflict without mutation when the message has started, been removed, or changed since it was read. Removal SHALL retain a cancelled accepted-turn history entry. Editing SHALL NOT replace the originally captured context with the currently selected page context.

The learner SHALL also be able to reorder the ordinary queued messages or send one of them now. Reorder SHALL atomically compare the complete expected pending order with the current order under the same dispatch ownership lock, accept only a permutation of exactly the queued entries, and preserve message identities, text and contexts. A stale order or an ineligible entry SHALL conflict without partial mutation.

Send-now SHALL atomically validate the target queued message and expected revision, remove it from the ordinary queue and use the direct interrupt-and-send path. It SHALL preserve that accepted turn identity, its current edited text and original captured context, rather than creating a duplicate turn. Existing queued peers SHALL retain their relative order and remain paused. Repetition for the same already-promoted turn SHALL return the same accepted result without cancelling a later running turn or dispatching twice. Ordinary submission-identity reconciliation SHALL NOT itself promote an accepted message.

#### Scenario: Edit a queued message

- **WHEN** the learner edits a queued message using its current revision
- **THEN** the current text and revision change while its accepted identity, original submitted fields, queue position, and captured context remain unchanged

#### Scenario: Remove a queued message

- **WHEN** the learner removes a queued message using its current revision
- **THEN** it is retained in history as cancelled and is not sent to a provider

#### Scenario: Edit races with queue dispatch

- **WHEN** an edit or removal races with the queued message starting
- **THEN** the ownership lock makes one operation win; a stale or already-running mutation returns a conflict and does not change the executing message

#### Scenario: Resume a paused queue explicitly

- **WHEN** the learner continues a paused queue while no provider turn is running
- **THEN** the earliest eligible retained message starts, then later messages may continue after success

#### Scenario: New work does not resume an old queue

- **WHEN** a message is accepted with the queue action while older messages remain paused
- **THEN** the new message remains retained with them and does not implicitly continue the queue

#### Scenario: Reorder queued messages

- **WHEN** the learner submits an expected order B/C and new order C/B while both remain queued
- **THEN** the service commits C/B as both display and execution order without changing their text, identity or original context

#### Scenario: Reorder races with dispatch or another queue mutation

- **WHEN** an entry starts, a queued entry is added/removed, or another reorder wins before a stale reorder is committed
- **THEN** the stale operation returns a conflict, leaves the current order unchanged and does not mutate the executing turn

#### Scenario: Promote an edited queued message

- **WHEN** queued C has been edited and send-now is accepted at its current revision while A runs and B is queued
- **THEN** C is removed from ordinary queue order, A is captured for cancellation, C runs once after A releases ownership using its existing identity, edited text and original context, and B remains paused

#### Scenario: Send-now races with dispatch

- **WHEN** C has not already been promoted by this operation and ordinary dispatch starts C or its revision changes before send-now is accepted
- **THEN** the operation conflicts without cancelling another turn, duplicating C or removing a different queued message

#### Scenario: Repeat send-now after promotion

- **WHEN** the same send-now request for C is repeated after C was already promoted or started
- **THEN** the service returns C's existing result without another execution or cancellation target

#### Scenario: Send-now is blocked

- **WHEN** a pending approval or a different stop handoff blocks send-now
- **THEN** the request conflicts and the original message stays queued with its original text, context and order

### Requirement: Paper update approval pauses conversation dispatch

The Bridge SHALL retain an Agent-proposed existing-Paper update and its approval state in the existing conversation/turn artifacts without applying it. Before the proposing provider turn releases ownership to the next queued message, the Bridge SHALL persist the pending approval and pause that conversation's dispatch. Waiting for learner approval SHALL NOT keep a provider task running. While approval is pending, messages explicitly submitted with queue MAY be accepted into the paused queue with their captured context. Interrupt-and-send and send-now SHALL be rejected without creating or rerouting a queued item; queue continuation SHALL NOT bypass the decision.

Only the page's explicit learner-approval operation SHALL apply this proposed update through the existing Paper preview/confirmation and update rules. A stale impact SHALL cause no write and require refreshed impact plus another learner click. Cancellation SHALL cause no Paper write. Both approval and cancellation SHALL retain older queued messages and leave continuation manual. Repeated approval attempts SHALL NOT apply the update or reset progress twice.

Pending approval SHALL survive page reload/reopen and service recovery with dispatch paused and no automatic approval or replay. Workspace, conversation, proposing turn, target Paper and operation revision SHALL scope each decision. This integration SHALL NOT alter historical attempts/ratings, question entities, unrelated Papers or the existing direct manual CLI contract.

#### Scenario: A proposes a Paper update with B/C queued
- **WHEN** provider turn A completes with a Paper update requiring approval while B/C are queued
- **THEN** its pending approval is persisted and dispatch is paused before ownership handoff; B/C do not start even with the browser closed

#### Scenario: Approval is resolved
- **WHEN** the learner approves or cancels the pending operation
- **THEN** only a current valid approval may write the target Paper, B/C remain retained and paused, and explicit continuation is required

#### Scenario: New work is accepted during approval
- **WHEN** another message is accepted with queue while the conversation has a pending Paper approval
- **THEN** its text and submission context are retained without provider dispatch or implicit resolution of the approval

#### Scenario: Recover a pending operation
- **WHEN** the service recovers a conversation with a persisted pending Paper approval
- **THEN** the operation remains pending, the queue stays paused, and neither the Paper update nor a queued provider starts automatically

#### Scenario: Interrupt is refused during approval

- **WHEN** the learner submits interrupt-and-send or send-now while a Paper approval is pending
- **THEN** the operation conflicts without provider dispatch, Paper writes, or conversion of the interrupt into queued work; an existing queued send-now target remains unchanged

### Requirement: Bundled Lesson Kit drill skill

Lesson Kit SHALL distribute the material-bounded drill skill and its local
terminology together as a Bundled Lesson Kit Skill in its installed package.
Every new Pi process launched by the Lesson Kit Bridge, in print or RPC mode,
SHALL receive exactly one argument loading that bundled skill, including when
model-specific or pinned conversation arguments are selected. The Bridge SHALL
preserve other skills, flags, native configuration, authentication and session
continuity. It SHALL NOT install files in course folders or Pi global
configuration, or rewrite provider configuration or conversation records.

#### Scenario: Installed package launches Pi

- **WHEN** an installed wheel launches Pi through the Bridge
- **THEN** the skill and terminology are available from package resources
- **AND** an absolute skill argument loads the packaged directory without manual copying

#### Scenario: Legacy managed skill argument

- **WHEN** selected Pi arguments contain the exact previously managed Lesson Kit skill directory or the bundled directory
- **THEN** the launch replaces duplicate managed skill arguments with one bundled argument
- **AND** unrelated skill paths, other flags and stored configuration remain unchanged

#### Scenario: Preserve existing process resources

- **WHEN** a Pi conversation process is already running during an upgrade
- **THEN** it keeps its current resources until a new conversation or normal idle recycling
- **AND** active work is not interrupted to reload the skill

