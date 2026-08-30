## ADDED Requirements

### Requirement: Ingest batch registry visibility

The workbench SHALL expose a read-only CLI listing of recorded ingest
batches (`ingest batches`), reporting for each batch its id, kind, item
counts, applied timestamp, rollback state, and backup path, newest first.
The listing SHALL perform zero writes and SHALL NOT require any prior
artifact, so that agents and the owner can discover batch ids for whole-batch
rollback.

#### Scenario: List recorded batches

- **WHEN** a caller runs the batch listing after two applies, one of them
  rolled back
- **THEN** both batches are reported newest first with their kind, counts,
  and rollback state, and the rolled-back batch is marked as such

#### Scenario: Listing performs zero writes

- **WHEN** the batch listing runs over any pool
- **THEN** database contents and row counts remain identical before and after
