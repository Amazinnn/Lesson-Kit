## ADDED Requirements

### Requirement: Micro quiz content contract

The pool SHALL store micro quizzes as formal problems carrying an explicit
`practice_modes` marking and a structured `micro_quiz` payload with quiz type
(`yes_no`, `single_choice`, `multiple_choice`, `closest_answer`,
`short_answer`), optional options, an answer key, an error reason, and source
evidence. A micro quiz SHALL map to exactly one knowledge point. The system
SHALL NOT truncate long formal problems into micro quizzes and SHALL NOT infer
micro-quiz content from legacy problem-type values.

#### Scenario: A well-formed micro quiz enters the pool

- **WHEN** a manifest item satisfies the contract for its quiz type
- **THEN** it is stored as a problem row whose payload preserves every
  supplied field and whose readable id follows the existing sequence rules

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, exceeds the stem length bound,
  has options that do not contain its answer key, or maps to several
  knowledge points
- **THEN** the deterministic gate rejects that item and nothing is written

### Requirement: Explicit mode marking

Formal problems without a `practice_modes` marking SHALL remain exam-only.
Flash Card and Yes/No pulls SHALL return only problems explicitly marked for
those modes, and SHALL report unfilled demand as shortage instead of
substituting unmarked content.

#### Scenario: Flash card pull with marked content

- **WHEN** a Flash Card pull runs over knowledge points holding marked
  micro quizzes
- **THEN** only marked items are returned in the existing pull result shape

#### Scenario: Flash card pull without marked content

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

The practice page SHALL render micro quizzes by quiz type: yes/no buttons,
option selection, or text answer; Flash Card sessions SHALL reveal the answer
before rating. Objective items SHALL be compared locally against the answer
key with the error reason shown, while the student's rating flow and all
learning-write semantics stay unchanged. Items without a micro-quiz payload
SHALL render exactly as before.

#### Scenario: Answer a yes/no item

- **WHEN** the student answers a yes/no micro quiz
- **THEN** the page shows whether the submitted choice matches the answer
  key together with the error reason, and the session records the result
  through the existing rating and learning-write paths

#### Scenario: Unmarked or ordinary problem

- **WHEN** a pulled problem has no micro-quiz payload
- **THEN** the practice page renders the existing exam flow unchanged
