## MODIFIED Requirements

### Requirement: Micro quiz content contract

The pool SHALL store micro quizzes as formal problems carrying an explicit
`practice_modes` marking and a structured `micro_quiz` payload with quiz type
(`yes_no`, `single_choice`, `multiple_choice`), options, an answer key, an
error reason, and source evidence. Every micro quiz type SHALL present
clickable options; free-text answering SHALL NOT be part of the contract. A
micro quiz SHALL map to exactly one knowledge point. Manifest items MAY carry
optional label fields `topic_label` (at most 40 characters),
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
