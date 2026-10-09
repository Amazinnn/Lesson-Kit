## MODIFIED Requirements

### Requirement: Practice session

A workbench practice session SHALL present one problem at a time from a
weak-point-first, non-repeating queue. Before the first pull the learner SHALL
choose per-problem or end-of-session self-rating, unless the learner's
show-rating preference is off, in which case the session starts with the rating
mode `off` and no self-rating surface appears during the round. Merely showing
a problem, drafting, revealing a solution, skipping, or ending a session SHALL
NOT write learning records — except that in an `off` session, an objective
problem's recorded verdict SHALL write the derived learning conclusion (对 →
mastered, 错 → wrong) to progress, current state, and schedule exactly once,
without a rating event. A learner-requested Agent attempt CLI operation MAY
record the active answer and an optional 1–5 learning rating. Scheduling SHALL
never lock a problem.

#### Scenario: Skip a problem without a learning record

- **WHEN** the learner skips the current problem
- **THEN** the next unseen problem is shown and no learner-state table is
  changed

#### Scenario: Explicit rating records a learning conclusion

- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** the feedback, derived learner state, and schedule are persisted once

#### Scenario: Answer a problem in a session

- **WHEN** the learner completes a problem and explicitly submits a rating
- **THEN** the next unseen problem is shown after the single feedback write

#### Scenario: An off session derives the conclusion from the verdict

- **WHEN** a session with the rating mode `off` records an objective attempt
  whose verdict is false
- **THEN** the problem's progress becomes wrong and its schedule advances from
  that conclusion exactly once, and no rated feedback event is written

#### Scenario: An off session records a subjective attempt without deriving

- **WHEN** a session with the rating mode `off` records a subjective attempt
- **THEN** the attempt is stored and no learning conclusion is derived

#### Scenario: An off session starts without a rating choice

- **WHEN** the learner starts a round while the show-rating preference is off
- **THEN** the round begins without the learner choosing a rating timing, and
  the stored rating mode is `off`

#### Scenario: Practice an un-due problem

- **WHEN** the learner selects a problem that is not yet due
- **THEN** it is shown and practiced normally with no lock or refusal

#### Scenario: Agent records at the learner's request

- **WHEN** the learner asks the Agent to record the active answer
- **THEN** only the explicit attempt CLI call writes it; viewing or discussing
  the draft alone does not
