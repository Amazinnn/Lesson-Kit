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
