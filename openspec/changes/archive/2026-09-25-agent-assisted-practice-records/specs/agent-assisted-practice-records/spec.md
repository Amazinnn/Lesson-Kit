## ADDED Requirements

### Requirement: Workspace attempt CLI

The workbench SHALL expose `lesson-kit attempts <workspace>` with `list`,
`get`, `check`, `apply`, and `correct` actions. List/get SHALL return structured
problem-attempt records without writing. Check/apply/correct SHALL accept UTF-8
JSON through `--input <file|->`; one manifest MAY contain one or many attempts.
Check SHALL validate and preview without writing. Apply SHALL commit all named
attempts and their permitted learning effects in one transaction or write none.
The CLI SHALL return attempt ids and actual outcomes; nonzero failures SHALL
carry actionable errors. Repeating an identical apply request SHALL return the
original result rather than insert duplicate attempts; reusing its request id
for different content SHALL fail.

#### Scenario: Agent previews and records two answers

- **WHEN** the Agent checks a valid two-attempt manifest and then applies it
- **THEN** check writes nothing and apply returns two readable attempt records from one atomic operation

#### Scenario: One invalid attempt protects the batch

- **WHEN** any item names an unknown problem or has an invalid rating
- **THEN** apply returns nonzero with an itemized error and no attempt, event, signal, state, or schedule change

#### Scenario: Retry after a lost CLI response

- **WHEN** the identical request id and manifest are applied twice
- **THEN** the second response returns the first result with no duplicate attempt or learning effect

### Requirement: Agent transcription and optional learning rating

An attempt manifest SHALL carry a problem id, transcribed answer text, a
natural-language grading note, and an optional integer 1–5 learning rating.
The rating represents the existing learning self-rating scale, not exam marks.
When present, the attempt, linked feedback event, learner signals, problem and
knowledge-point current states, progress, and schedule SHALL change atomically
through the existing rules. When absent, the submitted attempt and note SHALL
remain available without a feedback event or any signal, current-state,
progress, or schedule change. The system SHALL NOT add a grader identity field.

#### Scenario: Agent grades a handwritten proof

- **WHEN** a learner asks the Agent to record and grade a proof answer and the Agent applies a rating of 2
- **THEN** the transcription and note are retained once and the existing 2-rating learning effects apply once

#### Scenario: Incomplete answer cannot be rated

- **WHEN** the Agent submits a partial transcription and note without a rating
- **THEN** one ungraded attempt is retained and due dates and weakness evidence remain unchanged

### Requirement: Explicit attempt correction

Ordinary apply SHALL create a new attempt even when that problem has earlier
attempts. `correct` SHALL target an exact attempt id and replace its text,
note, and optional rating without creating a correction-history entry. The
operation SHALL withdraw the former rating's linked effects and recompute the
affected learning projections from the replacement within one transaction.
Correction SHALL refuse to overwrite an earlier attempt when later learning
actions have changed any affected projection; it SHALL leave every row
unchanged and explain that the learner may record a new attempt instead.

#### Scenario: Correct the latest rated attempt

- **WHEN** the Agent corrects the latest attempt's transcription and rating
- **THEN** the attempt id remains stable and its feedback, signals, progress, current states, and due date reflect the new rating exactly once

#### Scenario: Later learning blocks retrospective overwrite

- **WHEN** a specified attempt is followed by another attempt, feedback, or state/schedule change affecting its problem or linked knowledge points
- **THEN** correction is rejected with zero writes rather than rewriting subsequent learning history

### Requirement: Answer-image discovery without image retention

The learner SHALL be able to configure one or more answer-image directories
for a workspace through the CLI. The Agent MAY use its existing file tools to
locate and read images in those directories and the rest of its accessible
workspace. Lesson Kit SHALL NOT copy or archive answer-image bytes, save their
individual paths on attempts, or maintain a per-image scan index. Image
association and transcription are supplied by the Agent to the attempt CLI.
The system makes no cross-scan exact-image deduplication guarantee.

#### Scenario: Learner configures a folder

- **WHEN** a learner adds and lists an answer-image directory for a workspace
- **THEN** the CLI returns that directory for Agent discovery without creating a learning attempt

#### Scenario: Record from a multi-page answer

- **WHEN** the Agent reads several answer images and submits one transcription for a problem
- **THEN** the attempt stores the submitted text, note, and optional rating but no image bytes or per-image path
