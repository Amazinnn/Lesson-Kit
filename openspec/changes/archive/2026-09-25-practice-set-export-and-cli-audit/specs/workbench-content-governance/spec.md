## MODIFIED Requirements

### Requirement: Problem provenance axes

Every new Agent-managed problem or micro quiz SHALL declare `source_kind` for
its underlying material and `origin_kind` as `source_problem`,
`adapted_problem`, or `generated_grounded`. Generated content SHALL NOT use a
quiz/exam source value merely to describe its interaction form. A problem MAY
additionally declare `exam_year`, the optional study year of its source
examination (`2023`, `2023-2024秋冬`); when present it SHALL start with a
four-digit year and SHALL be at most 20 characters, and when absent the field
SHALL stay empty without affecting any other field.

#### Scenario: Generated micro quiz grounded in a textbook

- **WHEN** an Agent creates a micro quiz from textbook knowledge-point content
- **THEN** it records `source_kind=textbook` and `origin_kind=generated_grounded`

#### Scenario: Missing provenance is rejected

- **WHEN** Agent-managed problem content omits either provenance axis
- **THEN** the content gate rejects it and writes nothing

#### Scenario: Exam year is optional

- **WHEN** a problem is created without an exam year
- **THEN** it is accepted with the field empty and every other field is unaffected

#### Scenario: An invalid exam year is rejected

- **WHEN** Agent-managed problem content declares an exam year that does not start with a four-digit year or exceeds the length bound
- **THEN** the content gate rejects it and writes nothing
