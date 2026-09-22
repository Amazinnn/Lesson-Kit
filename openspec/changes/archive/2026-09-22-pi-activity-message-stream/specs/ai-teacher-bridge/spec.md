## MODIFIED Requirements

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
