## MODIFIED Requirements

### Requirement: Practice session

A workbench practice session SHALL present one problem at a time from a
weak-point-first, non-repeating queue. The learner SHALL choose per-problem or
end-of-session self-rating before the first pull. Merely showing a problem,
drafting, revealing a solution, skipping, or ending a session SHALL NOT write
learning records. A learner-requested Agent attempt CLI operation MAY record
the active answer and an optional 1–5 learning rating. Scheduling SHALL never
lock a problem.

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
- **THEN** it is shown and practiced normally with no lock or refusal

#### Scenario: Agent records at the learner's request

- **WHEN** the learner asks the Agent to record the active answer
- **THEN** only the explicit attempt CLI call writes it; viewing or discussing the draft alone does not

### Requirement: Flexible feedback

Feedback SHALL preserve a natural-language note and optional 1–5 learning
rating. A learner self-rating or a learner-requested Agent rating MAY record a
learning conclusion. A rating SHALL use the same signal and schedule rules,
independent of who submitted it. Navigation and unfinished work SHALL NOT
request or create a feedback log.

#### Scenario: Rate mastery without text

- **WHEN** the learner submits a rating of 2 without a note
- **THEN** the corresponding knowledge-point signal is raised and one feedback event is appended

#### Scenario: Describe a weakness in words

- **WHEN** the learner submits a rating with a natural-language note about a confusion
- **THEN** the note is preserved verbatim, mapped through existing signal rules, and one event is appended

#### Scenario: Skip feedback entirely

- **WHEN** the learner leaves a problem without submitting a rating or requesting Agent recording
- **THEN** the session continues without a new feedback, attempt, signal, progress, or schedule write

#### Scenario: Describe a weakness with a submitted rating

- **WHEN** the learner submits a rating and a natural-language note
- **THEN** the note is preserved verbatim and mapped through the existing signal rules

### Requirement: Grading input modes

Machine-gradable choice and true/false content SHALL retain its existing
automatic verdict. Open problems SHALL continue to support answer, reveal,
then learner self-rating. The learner MAY instead ask an Agent to transcribe
and grade the answer through the attempt CLI. An answer whose learning rating
cannot be determined MAY be recorded without a rating and SHALL NOT regress
the schedule.

#### Scenario: Auto-grade a choice problem

- **WHEN** the learner selects an option for a machine-gradable problem
- **THEN** the system grades it correct or wrong and records the graded attempt

#### Scenario: Reveal-then-rate an open problem

- **WHEN** the learner submits text for an open problem
- **THEN** the solution is revealed, the learner self-rates, and the attempt records the answer text and rating

#### Scenario: Record without grading

- **WHEN** the learner or Agent records an answer without a learning rating
- **THEN** the attempt is retained without changing signals, current states, progress, or schedule

### Requirement: Answer text capture for open problems

The practice page SHALL provide an answer box for open problems. A learner's
explicit rated submission or learner-requested Agent attempt CLI call SHALL
store the answer text. The latest recorded answer SHALL be available to later
authoritative Agent context. Unsubmitted drafts SHALL remain unwritten.

#### Scenario: Attach a design attempt to its record

- **WHEN** the learner submits a design answer with an explicit rating
- **THEN** the attempt stores the answer text and later Agent context includes it

#### Scenario: Agent transcribes a photographed answer

- **WHEN** the learner asks the Agent to record a photographed open answer
- **THEN** later Agent context can read the transcription without a stored answer-image attachment
