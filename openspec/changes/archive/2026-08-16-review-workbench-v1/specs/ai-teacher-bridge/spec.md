## Purpose

The AI teacher bridge connects the workbench to an external agent CLI without
embedding an AI kernel: tasks carry an output contract, run asynchronously, and
are validated before their results are trusted.

## ADDED Requirements

### Requirement: Provider configuration

The bridge SHALL read provider definitions (command, arguments, working
directory mode, timeout) from a config file, and the workbench SHALL expose
provider configuration as a CLI operation.

#### Scenario: Configure a provider

- **WHEN** the user runs `wb bridge add <provider> --command <cmd>`
- **THEN** the provider is written to the bridge config and listed as available for AI operations

### Requirement: Task lifecycle

An AI operation SHALL be a task with a durable state machine
(queued, running, done, failed), a task file describing the operation and its
context, a result file, and a status file. Status SHALL be queryable by the web
shell and the CLI while the task runs.

#### Scenario: Start and poll an explain task

- **WHEN** the user requests an explanation for a problem
- **THEN** a task is created in queued state and its status can be polled until it reaches done or failed

#### Scenario: Task failure is observable

- **WHEN** the external CLI exits non-zero or times out
- **THEN** the task transitions to failed and the failure reason is queryable and shown in the UI

### Requirement: Output-contract validation

The bridge SHALL NOT trust raw model output. A completed task SHALL be
validated against its output contract — result file written, required sections
present, source reference present, parseable Markdown — before it transitions
to done. Validation failure SHALL produce a failed state with the reason.

#### Scenario: Output missing a required section

- **WHEN** the agent result lacks a required section such as the source reference
- **THEN** the task fails with a reason naming the missing section and the result is not shown as authoritative

### Requirement: Explain operation

The v1 bridge SHALL support exactly one operation: `explain`. The task context
SHALL include the problem text, its solution, its knowledge-point links, the
learner's note, and current weak signals; the task SHALL be executed with the
workspace folder as working directory and its result SHALL be written under the
workspace's intermediate directory.

#### Scenario: Explain a problem the learner got wrong

- **WHEN** the learner requests an explanation for a wrong problem with a note about the sticking point
- **THEN** the task context includes problem, solution, linked knowledge points, the note, and weak signals, and the validated result is stored under the workspace intermediate directory and shown in the UI

### Requirement: Teacher conduct contract

Every explain task SHALL carry the teacher conduct rules in its instruction
text: establish what the learner already knows before explaining, explain in
focused and concise chunks, verify understanding with a question, never guess —
verify against the workspace pool and the source material — and cite the source
location. The conduct rules are part of the task contract, not of the
workbench's own logic.

#### Scenario: Task instruction includes conduct rules

- **WHEN** a task instruction file is generated for an explain operation
- **THEN** it contains the conduct rules (baseline question, concise explanation, comprehension check, no-guessing with source citation)

### Requirement: Workbench operates without AI

The workbench SHALL be fully functional with no provider configured and no AI
operation ever run: registry, weak list, pull, practice, feedback, and
scheduling SHALL work identically with or without the bridge.

#### Scenario: Practice without any provider

- **WHEN** no bridge provider is configured and the learner practices problems
- **THEN** every non-AI feature works unchanged and AI actions are shown as unavailable rather than broken

### Requirement: Diagnose operation

The bridge SHALL support a second operation, `diagnose`, in addition to
`explain`. A diagnose task SHALL include the learner's own answer text and any
step-stuck marking in its context, and its teacher conduct SHALL locate the
specific error or stuck point before explaining, give a next-step hint rather
than the full solution, and end with a comprehension question. The diagnose
output contract SHALL require the sections 定位 (location), 提示 (hint), 溯源
(source reference), and 追问 (follow-up question).

#### Scenario: Diagnose a wrong design

- **WHEN** the learner pastes their own design, marks the result wrong, and starts a diagnose task
- **THEN** the task context includes the design text and the marked step, and the validated result contains all four required sections with the hint section stopping short of the full solution

#### Scenario: Diagnose output missing a section

- **WHEN** a diagnose result lacks the 溯源 section
- **THEN** the task fails contract validation and the result is not shown as authoritative

### Requirement: Bridge artifact locations

Task working files SHALL live under the workspace's `.lessonkit/jobs/<job-id>/`
directory (task, instruction, status, and log files) and SHALL be excluded from
version control. Validated explain and diagnose results SHALL be written under
the workspace's `.lessonkit/explain/{course}/{chapter}/{item_id}.md` and SHALL
be tracked in version control as learning assets.

#### Scenario: Explain result lands in the explain area

- **WHEN** an explain task passes contract validation
- **THEN** the result file is written to `.lessonkit/explain/{course}/{chapter}/{item_id}.md` and the task working files remain under `.lessonkit/jobs/<job-id>/` outside version control

### Requirement: CLI is a data interface, not a teacher

The super CLI SHALL expose only data operations — query pool content, pull
problems, record attempts and feedback, start bridge tasks, read task status —
and SHALL carry no teaching semantics. Teaching behavior (how to teach, when to
ask, how to close a topic) SHALL live in the teaching layer (skills and the
teacher conduct contract), never in the CLI. The same teaching capability SHALL
be reachable through the web shell, whose AI panel is a thin conversation
surface over the same bridge tasks.

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
