## ADDED Requirements

### Requirement: Evaluation record management

An evaluation is one `feedback_events` row carrying an optional 1–5 rating and an
optional natural-language note for a problem, knowledge point, or card. The
Agent SHALL be able to add, list, get, update, and delete evaluations through
`lesson-kit feedback`. `update` and `delete` SHALL be allowed for any evaluation,
regardless of whether the browser or the Agent first wrote it. Before update or
delete, the call SHALL read the current evaluation and supply its expected rating
and note; a mismatch SHALL return a conflict and write nothing.

`update` SHALL rewrite only the row's rating and note. `delete` SHALL remove only
that row. Neither SHALL replay signals, current states, problem progress, or
schedule. `attempts correct` remains the whole-attempt replacement path that
withdraws and recomputes the linked effects. When the learner asks the Agent to
record, import, or manage an evaluation, the Agent MAY choose the rating;
ordinary tutoring without that request remains zero-write. Adding an evaluation
linked to an attempt that already has one SHALL be refused and return the
existing event id.

#### Scenario: Agent edits a learner-written evaluation

- **WHEN** the learner asks the Agent to change a rating the learner previously saved in the browser
- **THEN** the Agent reads the current evaluation, supplies the matching expected rating and note, and the same row is updated in place

#### Scenario: A stale expected value is refused

- **WHEN** the supplied expected rating or note no longer matches the current row
- **THEN** the call returns a conflict and writes no evaluation, signal, state, progress, or schedule

#### Scenario: Agent deletes the same evaluation

- **WHEN** the learner asks the Agent to remove an evaluation it or the learner wrote
- **THEN** the row is hard-deleted and derived projections are left as previously computed

#### Scenario: Agent chooses the rating

- **WHEN** the learner asks the Agent to record or evaluate an answer without supplying a 1–5 value
- **THEN** the Agent may choose the rating and record it through the evaluation or attempt path

#### Scenario: Duplicate attempt evaluation is refused

- **WHEN** an added evaluation names an attempt that already has one
- **THEN** the call writes nothing and returns the existing event id for an update

#### Scenario: Knowledge-point and card evaluations use the same path

- **WHEN** the Agent lists, updates, or deletes an evaluation for a knowledge point or card
- **THEN** the same read-before-write and hard-delete rules apply

#### Scenario: An edited evaluation does not replay projections

- **WHEN** an existing 2-rating evaluation is changed to 5 through the evaluation path
- **THEN** only the rating and note change; the previously derived signals, current state, progress, and schedule are not replayed
