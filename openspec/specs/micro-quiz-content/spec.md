# micro-quiz-content Specification

## Purpose

Define the micro-quiz content unit that fills the Micro and Yes/No mode
shells: a short-stem, fast-feedback card over one atomic knowledge point with
an explicit practice-mode marking, a structured payload (quiz type, options,
answer key, error reason, source evidence), a deterministic-gate ingest recipe
into the formal pool, and type-aware practice rendering with local objective
grading with clickable options for every type. Micro quizzes never come from
truncating long problems, and ordinary (unmarked) pool content stays exam-only.

## Requirements

### Requirement: Micro quiz content contract

The pool SHALL store micro quizzes as formal problems carrying an explicit
`practice_modes` marking and a structured `micro_quiz` payload with quiz type
(`yes_no`, `single_choice`, `multiple_choice`), options, an answer key, an
error reason, and source evidence. Every micro quiz type SHALL present
clickable options; free-text answering SHALL NOT be part of the contract. A
micro quiz SHALL map to exactly one knowledge point. The system SHALL NOT
truncate long formal problems into micro quizzes, SHALL NOT infer micro-quiz
content from legacy problem-type values, and SHALL NOT accept the retired
types `closest_answer` and `short_answer` at the gate.

#### Scenario: A well-formed micro quiz enters the pool

- **WHEN** a manifest item satisfies the contract for its quiz type
- **THEN** it is stored as a problem row whose payload preserves every
  supplied field and whose readable id follows the existing sequence rules

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, exceeds the stem length bound, has
  options that do not contain its answer key, maps to several knowledge
  points, or uses a retired quiz type
- **THEN** the deterministic gate rejects that item and nothing is written

### Requirement: Explicit mode marking for Micro and Yes/No

Formal problems without a `practice_modes` marking SHALL remain exam-only.
Micro and Yes/No pulls SHALL return only problems explicitly marked for those
modes (`single_choice`/`multiple_choice` marked for `micro`, `yes_no` marked
for `yes_no`), and SHALL report unfilled demand as shortage instead of
substituting unmarked content.

#### Scenario: Micro pull with marked content

- **WHEN** a Micro pull runs over knowledge points holding marked micro
  quizzes
- **THEN** only marked items are returned in the existing pull result shape

#### Scenario: Micro pull without marked content

- **WHEN** no marked item exists for the selected scope
- **THEN** the pull reports shortage and the entry keeps its empty state

### Requirement: Composable micro-quiz ingestion

Micro quizzes SHALL enter the pool only through the composable ingest recipe:
a manifest artifact, a deterministic contract gate, a recoverable backup, and
one explicit transactional apply. A failed apply SHALL leave the pool
unchanged.

#### Scenario: Apply a valid manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all items are inserted in one committed transaction after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** any statement inside the apply transaction fails
- **THEN** the whole apply rolls back and the pool keeps its prior content

### Requirement: Type-aware practice rendering

The practice page SHALL render micro quizzes by quiz type with clickable
options for every type: yes/no buttons, single-choice radios, or
multiple-choice checkboxes. Micro sessions SHALL reveal the answer and error
reason before rating, and the free-text answer box SHALL NOT be shown for
option-based items. Objective items SHALL be compared locally against the
answer key with the error reason shown, while the student's rating flow and
all learning-write semantics stay unchanged. Session-end rating cards SHALL
show the micro-quiz answer key and error reason instead of a formal solution.
Items without a micro-quiz payload SHALL render exactly as before.

#### Scenario: Answer a yes/no item

- **WHEN** the student answers a yes/no micro quiz
- **THEN** the page shows whether the submitted choice matches the answer
  key together with the error reason, and the session records the result
  through the existing rating and learning-write paths

#### Scenario: Answer a choice item

- **WHEN** the student answers a single- or multiple-choice micro quiz
- **THEN** the page grades the submitted options locally, shows the verdict
  with the error reason, and records the result through the existing rating
  and learning-write paths

#### Scenario: Unmarked or ordinary problem

- **WHEN** a pulled problem has no micro-quiz payload
- **THEN** the practice page renders the existing exam flow unchanged
