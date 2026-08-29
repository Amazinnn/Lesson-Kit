## MODIFIED Requirements

### Requirement: Composable flash-card ingestion

Flash cards SHALL enter the pool only through a composable ingest recipe: a
manifest artifact of kind `flash-card-patch`, a deterministic contract gate,
a recoverable backup, and one explicit transactional apply. Card ids SHALL
follow `^[a-z0-9-]+-fc-\d{3}$` and SHALL be unique, including against ids
already in the pool. A failed apply SHALL leave the pool unchanged. Every
apply SHALL record one readable sequential batch id and stamp every inserted
card row with it, enabling whole-batch rollback as defined by the content
governance capability.

#### Scenario: Apply a valid card manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all cards are inserted in one committed transaction after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** any statement inside the apply transaction fails
- **THEN** the whole apply rolls back and the pool keeps its prior content

#### Scenario: Applied cards carry the batch id

- **WHEN** a gate-passed card manifest is applied
- **THEN** every inserted card row carries the recorded batch id
