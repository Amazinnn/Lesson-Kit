# agent-assisted-practice-records Specification

## Purpose

Let the learner hand the Agent what they wrote on paper — a photographed
proof, a scanned derivation — and have it become a real practice record: the
`lesson-kit attempts` CLI transcribes the answer, optionally attaches the
learner's own 1–5 rating, and links the attempt to the same four-piece learning
write a browser self-rating uses. Everything here is explicit and idempotent:
one manifest can carry several problems, a request id makes a resend safe, an
attempt that was never rated still counts as a record, a correction replaces
one attempt in place, and the answer images stay in the learner's own
directories — registered read-only, never copied into the pool.
## Requirements
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
knowledge-point current states, learning progress, and schedule SHALL change
atomically through the existing rules. When absent, the submitted attempt and
note SHALL remain available without a feedback event or any signal,
current-state, learning-progress, or schedule change. Paper execution progress
MAY additionally change when the manifest names a `paper_id`, under the
Paper-bound attempt import requirement; that execution progress is not a
learning projection. The system SHALL NOT add a grader identity field.

#### Scenario: Agent grades a handwritten proof

- **WHEN** a learner asks the Agent to record and grade a proof answer and the Agent applies a rating of 2
- **THEN** the transcription and note are retained once and the existing 2-rating learning effects apply once

#### Scenario: Incomplete answer cannot be rated

- **WHEN** the Agent submits a partial transcription and note without a rating
- **THEN** one ungraded attempt is retained, Paper execution progress may be updated, and due dates and weakness evidence remain unchanged

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

### Requirement: Paper-bound attempt import

An attempt manifest MAY carry an optional top-level `paper_id` naming one saved
Paper. When present, every item SHALL name a problem that belongs to that
Paper's current ordered items, and the whole batch SHALL be rejected with zero
writes if the Paper, its current validation, or any item is invalid. Apply SHALL
record the attempts and bind each named problem to that Paper's execution
progress in the same transaction: the active execution when the Paper is the
selected one, the Paper's parked checkpoint when one exists, or a newly created
parked checkpoint when the Paper has no unfinished progress.

A newly created checkpoint SHALL use `reveal_timing = on_submit`, SHALL allocate
its own execution identity, and SHALL NOT create an active practice selection or
a `practice_runs` archive row. Binding SHALL set the item state to `answered`
and link the new attempt. An item that already had an answer or stuck mark SHALL
be re-bound to the new attempt without deleting, editing, or rewriting the
earlier attempt. Binding SHALL clear a pending answer draft and a stuck mark
while preserving any recorded reference-view fact. Importing into a Paper that
is not the selected Paper SHALL NOT pause, replace, or otherwise modify the
selected Paper's execution.

Completion SHALL follow the target execution's existing mode: a legacy selected
(active) execution whose last pending item becomes answered SHALL archive as
completed, while an explicit `per_item` or `on_submit` execution SHALL wait for
the learner's explicit Paper submission. The import itself SHALL NOT archive a
parked execution; a legacy Paper that was parked at import time keeps its
checkpoint and completes through the existing legacy rules on later
learner action. An ungraded import SHALL
change only Paper execution
progress and SHALL NOT change learning progress, signals, current states, or
schedule. Repeating an identical manifest SHALL return the original binding
result without creating another attempt or moving progress twice; reusing the
request id with a different Paper or item set SHALL fail.

#### Scenario: Bind to a parked Paper without touching the selected Paper

- **WHEN** the manifest names a saved Paper that has parked progress while another Paper is selected
- **THEN** the imported attempts bind to the named Paper's checkpoint and the selected Paper's items, cursor, drafts, and attempts remain unchanged

#### Scenario: Create parked progress for a Paper with no unfinished work

- **WHEN** the manifest names a saved Paper with no active or parked execution
- **THEN** one `on_submit` checkpoint is created with the imported items answered, no active practice is created, and the saved Paper reads show the new progress

#### Scenario: Re-bind an item that already has an answer

- **WHEN** the manifest imports a problem that the target Paper already answered or marked stuck
- **THEN** a new attempt is appended, the item links to it, and the earlier attempt remains readable in history

#### Scenario: Ungraded import changes only execution progress

- **WHEN** an imported item has answer text or a note but no rating
- **THEN** only the Paper execution progress and attempt change; signals, current states, learning progress, and schedule do not

#### Scenario: Explicit mode waits for submission

- **WHEN** the last pending item of a `per_item` or `on_submit` Paper is imported as answered
- **THEN** the paper remains unfinished until the learner explicitly submits it

#### Scenario: Legacy last item archives

- **WHEN** the last pending item of a legacy selected Paper is imported as answered
- **THEN** that execution archives as completed exactly once under the existing legacy rule, while parked legacy Papers keep their checkpoints until the learner resumes them

#### Scenario: Invalid item protects the batch

- **WHEN** any item names a problem outside the Paper or the Paper fails current validation
- **THEN** no attempt, feedback event, execution item, checkpoint, or progress row changes

#### Scenario: Retry returns the original binding result

- **WHEN** the identical request id and manifest are applied twice
- **THEN** the second response returns the first attempt ids and binding result with no duplicate attempt or progress movement

