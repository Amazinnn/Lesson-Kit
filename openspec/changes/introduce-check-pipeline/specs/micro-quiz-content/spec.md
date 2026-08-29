## MODIFIED Requirements

### Requirement: Composable micro-quiz ingestion

Micro quizzes SHALL enter the pool only through the composable ingest recipe:
a manifest artifact, a deterministic contract gate, a recoverable backup, and
one explicit transactional apply. A failed apply SHALL leave the pool
unchanged. Every apply SHALL record one readable sequential batch id and
stamp every inserted problem row with it, enabling whole-batch rollback as
defined by the content governance capability.

#### Scenario: Apply a valid manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all items are inserted in one committed transaction after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** any statement inside the apply transaction fails
- **THEN** the whole apply rolls back and the pool keeps its prior content

#### Scenario: Applied micro quizzes carry the batch id

- **WHEN** a gate-passed micro-quiz manifest is applied
- **THEN** every inserted problem row carries the recorded batch id
