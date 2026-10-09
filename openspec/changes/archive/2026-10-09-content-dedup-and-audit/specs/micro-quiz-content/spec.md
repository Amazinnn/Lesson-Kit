## MODIFIED Requirements

### Requirement: Micro quiz content contract

The pool SHALL store micro quizzes as formal problems carrying an explicit
`practice_modes` marking and a structured `micro_quiz` payload with quiz type
(`yes_no`, `single_choice`, `multiple_choice`), options, an answer key, an
error reason, and source evidence. An objective item MAY enter without an
answer key when its source lost it: an absent or empty `answer_key` SHALL mark
the item keyless instead of being refused, the choice types SHALL still carry
2–6 options, `yes_no` SHALL keep its implied 是/否 options, and `error_reason`
SHALL be mandatory only for an item that carries a key. Every micro quiz type
SHALL present clickable options; free-text answering SHALL NOT be part of the
contract. A micro quiz SHALL map to exactly one knowledge point and SHALL NOT
be refused for stem length alone. Problem manifest items MAY carry optional
`display_title` (at most 80 characters) and `display_summary` (at most 200
characters); a supplied field SHALL be a non-empty string that passes the
shared markup safety check, and an omitted field is stored as null. Problem
manifests and edits SHALL NOT accept `topic_label`, which is a flash-card field
only. A problem that already exists in the pool SHALL be convertible into a
micro quiz in place, keeping its readable id and every learning record: the
conversion supplies `practice_modes` and the payload through the explicit
problem patch, the options MAY be lifted verbatim out of the old problem text,
and the same contract SHALL be enforced for the parts the patch touches. The
system SHALL NOT truncate long formal problems into micro quizzes, SHALL NOT
fabricate options a source does not have, SHALL NOT infer micro-quiz content
from legacy problem-type values, and SHALL NOT accept the retired types
`closest_answer` and `short_answer` at the gate.

#### Scenario: A well-formed micro quiz enters the pool

- **WHEN** a manifest item satisfies the contract for its quiz type
- **THEN** it is stored as a problem row whose payload preserves every
  supplied field and whose readable id follows the existing sequence rules

#### Scenario: A keyless objective item enters the pool

- **WHEN** a 判断题 or 单选题 manifest item declares its quiz type and options but carries no answer key
- **THEN** it is stored with its practice-mode marking, an empty answer key, and no error reason, and the import reports how many items arrived without a key

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, has options that do not contain its
  answer key, maps to several knowledge points, or uses a retired quiz type
- **THEN** the deterministic gate rejects that item and nothing is written

#### Scenario: Display field validation

- **WHEN** a manifest item supplies a display field that is empty after
  trimming, exceeds its bound, or fails the markup safety check
- **THEN** the deterministic gate rejects that item with an explicit reason;
  omitted display fields are accepted and stored as null

#### Scenario: A key can be supplied later

- **WHEN** the learner or the Agent fills in the answer key of a keyless item through the problem update path
- **THEN** the key is validated against that item's own quiz type and stored, and clearing it returns the item to keyless

#### Scenario: An existing problem becomes a micro quiz in place

- **WHEN** an explicitly requested patch gives an existing problem a quiz type, options, and its practice-mode marking
- **THEN** the row keeps its id and learning records, is pulled by the matching practice mode, and is no longer pulled by 综合题

#### Scenario: Objective items have no stem length bound

- **WHEN** a 判断题 or 单选题 carries a long multi-assertion stem or inlined option block
- **THEN** it stays in the matching practice mode and is not refused for its length

#### Scenario: A problem does not carry a topic label

- **WHEN** a problem or micro-quiz manifest is prepared
- **THEN** its supported display fields are `display_title` and
  `display_summary`, and `topic_label` is not part of the problem contract

#### Scenario: Flash cards retain their topic label

- **WHEN** a flash-card manifest supplies its optional `topic_label`
- **THEN** the flash-card contract validates and stores that field as specified
  by the `flash-card` capability

#### Scenario: Label field validation

- **WHEN** a manifest item supplies a label field that is empty after
  trimming, exceeds its bound, or fails the markup safety check
- **THEN** the deterministic gate rejects that item with an explicit reason;
  omitted label fields are accepted and stored as null

#### Scenario: The stem bound admits long objective items

- **WHEN** a 判断题 or 单选题 carries a stem of any length — multiple assertions, a
  long scenario, or a whole option block inlined in the text
- **THEN** it is stored as a micro quiz for its practice mode, with no length-based
  refusal at the ingest gate and no length-based refusal on the patch path
