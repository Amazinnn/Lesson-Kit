## ADDED Requirements

### Requirement: Agent evaluation management

When the learner explicitly asks the Agent to record, import, or manage an
evaluation, the Agent MAY list, add, update, or delete evaluations for problems,
knowledge points, and cards through `lesson-kit feedback`. Before an update or
delete, the Agent SHALL read the current evaluation and supply its expected
rating and note; a mismatch SHALL return a conflict and write nothing. The Agent
MAY choose the 1–5 rating itself; the learner does not need to supply a number.
Ordinary tutoring that does not ask for a record remains zero-write.

An update SHALL change only the evaluation row. A delete SHALL hard-delete only
that row. Neither SHALL replay learning projections; replacing the whole attempt
and recomputing its effects remains the `attempts correct` path.

#### Scenario: Manage a learner-written evaluation

- **WHEN** the learner asks the Agent to change or remove a rating the learner saved in the browser
- **THEN** the Agent reads the evaluation, supplies the expected values, and updates or deletes the same row

#### Scenario: Refuse a stale write

- **WHEN** the evaluation changed after the Agent read it
- **THEN** the write is refused without changing any row and the Agent rereads the current value

#### Scenario: Choose a score

- **WHEN** the learner asks the Agent to record and evaluate an answer without providing a score
- **THEN** the Agent may choose the rating and write it through the evaluation path

#### Scenario: Ordinary tutoring stays read-only

- **WHEN** the learner discusses an answer without asking to record or manage an evaluation
- **THEN** the Agent reads context but writes no evaluation, attempt, or learning projection
