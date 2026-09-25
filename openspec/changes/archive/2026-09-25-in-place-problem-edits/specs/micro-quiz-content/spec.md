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
contract. A micro quiz SHALL map to exactly one knowledge point, and its stem
SHALL be at most 800 characters. Manifest items MAY carry optional label fields
`topic_label` (at most 40 characters), `display_title` (at most 80 characters),
and `display_summary` (at most 200 characters); a supplied label field SHALL be
a non-empty string that passes the shared markup safety check, and an omitted
field is stored as null. A problem that already exists in the pool SHALL be
convertible into a micro quiz **in place**, keeping its readable id and every
learning record: the conversion supplies `practice_modes` and the payload
through the explicit problem patch, the options MAY be lifted verbatim out of
the old problem text, and the same contract SHALL be enforced for the parts the
patch touches. The system SHALL NOT truncate long formal problems into micro
quizzes, SHALL NOT fabricate options a source does not have, SHALL NOT infer
micro-quiz content from legacy problem-type values, and SHALL NOT accept the
retired types `closest_answer` and `short_answer` at the gate.

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

#### Scenario: An existing problem becomes a micro quiz in place

- **WHEN** an explicitly requested patch gives an existing problem a quiz type, options, and its practice-mode marking
- **THEN** the row keeps its id and learning records, is pulled by the matching practice mode, and is no longer pulled by 综合题

#### Scenario: The stem bound admits long objective items

- **WHEN** a 判断题 or 单选题 carries a stem of 800 characters or fewer
- **THEN** its length is not a contract violation, and a stem above 800 characters is still refused as long content
