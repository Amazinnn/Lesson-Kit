## MODIFIED Requirements

### Requirement: Type-aware practice rendering

The practice page SHALL render micro quizzes by quiz type with clickable
options for every type: yes/no buttons, single-choice radios, or
multiple-choice checkboxes. Micro sessions SHALL reveal the answer and error
reason before rating, and the free-text answer box SHALL NOT be shown for
option-based items. Objective items SHALL be compared locally against the
answer key with the error reason shown, while the student's rating flow and
all learning-write semantics stay unchanged. In unified (batch) rating mode
the locally computed verdict SHALL remain visible for a brief hold before
the session advances to the next item, and a wrong answer SHALL highlight
the correct option(s) during that hold; the hold SHALL NOT write any
feedback — ratings and learning writes still happen only at session end.
Session-end rating cards SHALL show the micro-quiz answer key and error
reason instead of a formal solution. Items without a micro-quiz payload
SHALL render exactly as before.

#### Scenario: Answer a yes/no item

- **WHEN** the student answers a yes/no micro quiz
- **THEN** the page shows whether the submitted choice matches the answer
  key together with the error reason, and the session records the result
  through the existing rating and learning-write paths

#### Scenario: Answer a choice item

- **WHEN** the student answers a single- or multiple-choice micro quiz
- **THEN** the page grades the submitted options locally, shows the verdict
  with the error reason, and records the result through the existing rating
  and learning-write paths

#### Scenario: Wrong answer in unified rating

- **WHEN** the student answers a choice or yes/no item wrongly in batch
  rating mode
- **THEN** the verdict with the error reason stays visible with the correct
  option(s) highlighted for a brief hold before the next item is pulled, and
  no feedback is written until the final review

#### Scenario: Correct answer in unified rating

- **WHEN** the student answers a choice or yes/no item correctly in batch
  rating mode
- **THEN** the verdict stays visible for the same brief hold before the
  session advances, with the same deferred rating semantics

#### Scenario: Unmarked or ordinary problem

- **WHEN** a pulled problem has no micro-quiz payload
- **THEN** the practice page renders the existing exam flow unchanged
