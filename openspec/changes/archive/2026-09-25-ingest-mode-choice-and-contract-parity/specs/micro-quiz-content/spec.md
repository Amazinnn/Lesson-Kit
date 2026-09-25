## MODIFIED Requirements

### Requirement: Micro quiz content contract

The pool SHALL store micro quizzes as formal problems carrying an explicit
`practice_modes` marking and a structured `micro_quiz` payload with quiz type
(`yes_no`, `single_choice`, `multiple_choice`), options, an answer key, an
error reason, and source evidence. An objective item MAY enter **without** an
answer key when its source lost it: an absent or empty `answer_key` SHALL mark
the item keyless instead of being refused, the choice types SHALL still carry
2–6 options, `yes_no` SHALL keep its implied 是/否 options, and `error_reason`
SHALL be mandatory only for an item that carries a key. Every micro quiz type
SHALL present clickable options; free-text answering SHALL NOT be part of the
contract. A micro quiz SHALL map to exactly one knowledge point. Manifest items
MAY carry optional label fields `topic_label` (at most 40 characters),
`display_title` (at most 80 characters), and `display_summary` (at most 200
characters); a supplied label field SHALL be a non-empty string that passes
the shared markup safety check, and an omitted field is stored as null. The
system SHALL NOT truncate long formal problems into micro quizzes, SHALL NOT
infer micro-quiz content from legacy problem-type values, and SHALL NOT
accept the retired types `closest_answer` and `short_answer` at the gate.

#### Scenario: A well-formed micro quiz enters the pool

- **WHEN** a manifest item satisfies the contract for its quiz type
- **THEN** it is stored as a problem row whose payload preserves every
  supplied field and whose readable id follows the existing sequence rules

#### Scenario: A keyless objective item enters the pool

- **WHEN** a 判断题 or 单选题 manifest item declares its quiz type and options but carries no answer key
- **THEN** it is stored with its practice-mode marking, an empty answer key, and no error reason, and the import reports how many items arrived without a key

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, exceeds the stem length bound, has
  options that do not contain its answer key, maps to several knowledge
  points, or uses a retired quiz type
- **THEN** the deterministic gate rejects that item and nothing is written

#### Scenario: Label field validation

- **WHEN** a manifest item supplies a label field that is empty after
  trimming, exceeds its bound, or fails the markup safety check
- **THEN** the deterministic gate rejects that item with an explicit reason;
  omitted label fields are accepted and stored as null

#### Scenario: A key can be supplied later

- **WHEN** the learner or the Agent fills in the answer key of a keyless item through the problem update path
- **THEN** the key is validated against that item's own quiz type and stored, and clearing it returns the item to keyless

### Requirement: Type-aware practice rendering

The practice page SHALL render micro quizzes by quiz type with clickable
options for every type: yes/no buttons, single-choice radios, or
multiple-choice checkboxes. Micro sessions SHALL reveal the answer and error
reason before rating, and the free-text answer box SHALL NOT be shown for
option-based items. Objective items that carry an answer key SHALL be compared
locally against it with the error reason shown, while the student's rating flow
and all learning-write semantics stay unchanged. An objective item without a key
SHALL NOT be graded: its submitted choice is still recorded, the page states
that no answer key is stored instead of reporting a verdict, and the item keeps
the existing rating path. In unified (batch) rating mode the locally computed
verdict SHALL remain visible for a brief hold before the session advances to the
next item, and a wrong answer SHALL highlight the correct option(s) during that
hold; the hold SHALL NOT write any feedback — ratings and learning writes still
happen only at session end. Session-end rating cards SHALL show the micro-quiz
answer key and error reason instead of a formal solution, and SHALL state that a
keyless item has no stored answer key. Items without a micro-quiz payload SHALL
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
