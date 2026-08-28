## MODIFIED Requirements

### Requirement: Problem pull engine
The pull engine SHALL require an explicit non-empty `kp_ids` scope and one
selected mode. It SHALL exclude the supplied `exclude_ids`, report shortage per
knowledge point, and SHALL never infer scope from weak ordering, due state, a
daily plan, or the full pool. Unmarked legacy problems remain available only to
`exam`; card and yes/no pulls require explicit content metadata.

#### Scenario: Pull within explicit scope
- **WHEN** the learner starts practice with selected knowledge points and mode
- **THEN** returned problems are linked to those points, honor exclusions, and
  are not repeated in the session

#### Scenario: Pull without scope
- **WHEN** `kp_ids` is empty or absent
- **THEN** the engine returns an empty handoff result and performs no implicit
  weak-item or full-pool selection

#### Scenario: Unsupported mode content
- **WHEN** a selected card or yes/no mode has no explicitly marked content
- **THEN** the engine reports shortage for that mode instead of downgrading to
  exam or fabricating metadata

#### Scenario: Pull problems for a weak knowledge point
- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered,
  with none repeated within the same session

#### Scenario: Pool shortage is reported
- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point instead of
  inventing problems

### Requirement: Practice session
A session SHALL have exactly one selected mode for its lifetime. Selection,
navigation, drafting, skipping, and plan viewing SHALL remain zero-write; only
the existing explicit rating/content/state operations persist learning records.

#### Scenario: Change mode mid-session
- **WHEN** a learner attempts to select another mode after starting
- **THEN** the session rejects the change and continues with its original mode

#### Scenario: Skip a problem without a learning record
- **WHEN** the learner skips the current problem
- **THEN** the next unseen problem is shown and no learner-state table changes

#### Scenario: Explicit rating records a learning conclusion
- **WHEN** the learner submits a 1-5 self-rating for a completed problem
- **THEN** feedback, derived learner state, and schedule are persisted once

#### Scenario: Answer a problem in a session
- **WHEN** the learner completes a problem and explicitly submits a rating
- **THEN** the next unseen problem is shown after the single feedback write

#### Scenario: Practice an un-due problem
- **WHEN** the learner selects a problem that is not yet due
- **THEN** it is shown and practiced normally, with no lock or refusal
