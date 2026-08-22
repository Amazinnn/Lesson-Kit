## MODIFIED Requirements

### Requirement: Practice session

A workbench practice session SHALL present one problem at a time from a weak-point-first, non-repeating session queue. The learner SHALL choose either per-problem self-rating or end-of-session unified self-rating before the first problem is pulled. Showing a problem, drafting an answer, revealing a solution, skipping a problem, or ending a session without an explicit rating SHALL NOT write an attempt, feedback event, signal, progress row, or schedule update. The schedule SHALL never lock a problem.

#### Scenario: Skip a problem without a learning record

- **WHEN** the learner skips the current problem
- **THEN** the next unseen problem is shown and no learner-state table is changed

#### Scenario: Explicit rating records a learning conclusion

- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** the feedback, derived learner state, and schedule are persisted once

#### Scenario: Answer a problem in a session

- **WHEN** the learner completes a problem and explicitly submits a rating
- **THEN** the next unseen problem is shown after the single feedback write

#### Scenario: Practice an un-due problem

- **WHEN** the learner selects a problem that is not yet due
- **THEN** it is shown and practiced normally, with no lock or refusal

### Requirement: Flexible feedback

Feedback SHALL consist of an optional natural-language note paired with an explicit 1–5 self-rating when the learner chooses to record a learning conclusion. A submitted rating SHALL preserve the note verbatim and update the existing signal and scheduling mechanisms. The workbench SHALL NOT request a feedback log for navigation or unfinished work.

#### Scenario: Rate mastery without text

- **WHEN** the learner submits a rating of 2 without a note
- **THEN** the corresponding knowledge-point signal is raised and one feedback event is appended

#### Scenario: Describe a weakness in words

- **WHEN** the learner submits a rating with a natural-language note about a confusion
- **THEN** the note is mapped to a signal type, stored verbatim on the signal, and one event is appended

#### Scenario: Skip feedback entirely

- **WHEN** the learner leaves a problem without submitting a rating
- **THEN** the session continues with no feedback, attempt, signal, progress, or schedule write

#### Scenario: Describe a weakness with a submitted rating

- **WHEN** the learner submits a rating and a natural-language note
- **THEN** the note is preserved verbatim and mapped through the existing signal rules

### Requirement: Current learning state

The workbench SHALL maintain one current state for each knowledge point or problem, selected from `needs_work`, `review`, and `mastered`. A submitted rating of 1–2, 3–4, or 5 SHALL respectively set that state. A learner's explicit graph-state edit SHALL replace only the current state and update scheduling through the corresponding rating without appending a feedback event or learner signal.

#### Scenario: Edit a graph state without creating a history event

- **WHEN** the learner changes a knowledge point from review to mastered in the graph
- **THEN** the current state and schedule are updated and feedback-event and learner-signal counts do not increase
