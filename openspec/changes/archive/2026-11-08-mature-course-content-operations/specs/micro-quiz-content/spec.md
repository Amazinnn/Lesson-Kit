## MODIFIED Requirements

### Requirement: Composable micro-quiz ingestion

Micro quizzes SHALL enter the pool only through the composable ingest recipe:
a manifest artifact, a deterministic contract gate, a recoverable backup, and
explicit consistent applies of independent valid units. A failed unit SHALL retain its prior state while independent valid units can complete. Every apply SHALL record one readable sequential batch id and
stamp every inserted problem row with it, preserving provenance under the content governance capability. Explicit successful-batch undo SHALL be retired.

#### Scenario: Apply a valid manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all valid items are inserted through consistent independent units after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** a statement inside an independent unit fails
- **THEN** the failed unit retains its prior state and independent committed units remain applied

#### Scenario: Applied micro quizzes carry the batch id

- **WHEN** a gate-passed micro-quiz manifest is applied
- **THEN** every inserted problem row carries the recorded batch id
