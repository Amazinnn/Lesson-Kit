## ADDED Requirements

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

Completion SHALL follow the target execution's existing mode: a legacy execution
whose last pending item becomes answered SHALL archive as completed, while an
explicit `per_item` or `on_submit` execution SHALL wait for the learner's
explicit Paper submission. An ungraded import SHALL change only Paper execution
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

- **WHEN** the last pending item of a legacy Paper is imported as answered
- **THEN** the execution archives as completed exactly once under the existing legacy rule

#### Scenario: Invalid item protects the batch

- **WHEN** any item names a problem outside the Paper or the Paper fails current validation
- **THEN** no attempt, feedback event, execution item, checkpoint, or progress row changes

#### Scenario: Retry returns the original binding result

- **WHEN** the identical request id and manifest are applied twice
- **THEN** the second response returns the first attempt ids and binding result with no duplicate attempt or progress movement

## MODIFIED Requirements

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
