## MODIFIED Requirements

### Requirement: Type-aware practice rendering

The practice page SHALL render micro quizzes by quiz type with clickable
options for every type: yes/no buttons, single-choice radios, or
multiple-choice checkboxes. Micro sessions SHALL reveal the answer key, the
error reason, and — when the problem carries a non-empty written solution —
that written solution before rating, and the free-text answer box SHALL NOT be
shown for option-based items. The written solution SHALL be presented in the
same explanation section the exam flow uses, labelled by the problem's
solution origin. Objective items that carry an answer key SHALL be compared
locally against it with the error reason shown, while the student's rating flow
and all learning-write semantics stay unchanged. An objective item without a key
SHALL NOT be graded: its submitted choice is still recorded, the page states
that no answer key is stored instead of reporting a verdict, and the item keeps
the existing rating path. In unified (batch) rating mode the locally computed
verdict SHALL remain visible for a brief hold before the session advances to the
next item, and a wrong answer SHALL highlight the correct option(s) during that
hold; the hold SHALL NOT write any feedback — ratings and learning writes still
happen only at session end. Session-end rating cards SHALL show the micro-quiz
answer key and error reason, SHALL also show the problem's written solution
when one is stored, and SHALL state that a keyless item has no stored answer
key; a card whose problem has no stored written solution SHALL fall back to the
key and error reason alone. Items without a micro-quiz payload SHALL
render exactly as before.

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

#### Scenario: Answer an item without a key

- **WHEN** the student answers an objective item whose answer key is not stored
- **THEN** no verdict is shown, the page says the item has no stored answer key, the submitted choice is still recorded, and the session's rating path is unchanged

#### Scenario: Reveal shows the stored written solution

- **WHEN** the student reveals a micro quiz whose problem carries a non-empty
  written solution
- **THEN** the reveal shows the answer key, the error reason, and the written
  solution in the explanation section with its solution-origin label, and the
  rating path is unchanged

#### Scenario: Reveal without a stored written solution

- **WHEN** the student reveals a micro quiz whose problem has no stored
  written solution
- **THEN** the reveal shows the answer key and error reason only, with no
  empty explanation section

#### Scenario: Session-end card shows the written solution

- **WHEN** a session ends on rating cards for micro-quiz items that carry a
  written solution
- **THEN** each card shows the answer key, the error reason, and the written
  solution, while solution-less items show only the key and error reason

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
