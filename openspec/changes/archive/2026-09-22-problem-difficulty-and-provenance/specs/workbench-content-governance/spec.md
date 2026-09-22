## REMOVED Requirements

### Requirement: Optional difficulty declaration

**Reason:** Difficulty no longer belongs to content ingest. It is a separate
lazy transaction governed by the `problem-difficulty` capability.

## ADDED Requirements

### Requirement: Problem provenance axes

Every new Agent-managed problem or micro quiz SHALL declare `source_kind` for
its underlying material and `origin_kind` as `source_problem`,
`adapted_problem`, or `generated_grounded`. Generated content SHALL NOT use a
quiz/exam source value merely to describe its interaction form.

#### Scenario: Generated micro quiz grounded in a textbook

- **WHEN** an Agent creates a micro quiz from textbook knowledge-point content
- **THEN** it records `source_kind=textbook` and `origin_kind=generated_grounded`

#### Scenario: Missing provenance is rejected

- **WHEN** Agent-managed problem content omits either provenance axis
- **THEN** the content gate rejects it and writes nothing
