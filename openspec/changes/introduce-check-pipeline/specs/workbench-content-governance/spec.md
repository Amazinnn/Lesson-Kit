## MODIFIED Requirements

### Requirement: Explicit content mutation boundary

Pool content SHALL change only after an explicit create, update, delete, state, gate, or promote command, or through the structured check ingest action defined by the ai-teacher-bridge capability. Browsing, search, navigation, draft text, ordinary Agent conversation, and provider tool events SHALL NOT mutate pool or learning data. After a successful Agent mutation, the teacher answer SHALL expose a concise object, action, and workbench-link summary rather than raw commands, SQL, or tool logs.

#### Scenario: Discuss a possible edit

- **WHEN** the learner discusses changing a knowledge point without explicitly asking to apply the change
- **THEN** the Agent may explain or propose the edit but no data command is issued

#### Scenario: Apply an explicit edit

- **WHEN** the learner explicitly requests a content change and the Agent completes it
- **THEN** the answer identifies the changed object and action with a workbench link and omits internal command logs

#### Scenario: Apply content through the bridge check action

- **WHEN** the learner explicitly asks in an Agent conversation to add pool content and the reply carries a valid check ingest action
- **THEN** the pool changes only through the same deterministic gate and batch-recorded apply as the CLI recipes

### Requirement: Composable ingestion commands

The workbench SHALL expose `prepare`, `run`, `gate`, `apply`, `render`, official `recipe`, and `rollback` ingestion commands that exchange explicit UTF-8 artifacts. Preparing work SHALL NOT start an Agent, running Agent work SHALL require an explicit available provider with no fallback, recipes SHALL perform no pool write unless the caller supplies `--apply`, and rollback SHALL act only on a recorded ingest batch.

#### Scenario: Prepare without invoking a provider

- **WHEN** a caller prepares a problem-solution task from a valid input artifact
- **THEN** the task artifact is written and no provider process or pool write occurs

#### Scenario: Run with one explicit provider

- **WHEN** a caller runs a prepared task with `--provider codex`
- **THEN** only Codex is invoked and a failure is returned without invoking Claude

#### Scenario: Preview an official recipe

- **WHEN** a caller runs an official recipe without `--apply`
- **THEN** validated output artifacts may be produced but database contents and row counts remain unchanged

#### Scenario: Resume from a qualified artifact

- **WHEN** a caller supplies an existing artifact that satisfies the next operation's contract
- **THEN** that operation runs without requiring preceding stages to be repeated

#### Scenario: Rollback only acts on a recorded batch

- **WHEN** a caller runs rollback for a batch id with no ingest-batch record
- **THEN** the command fails without writing and reports the unknown batch

## ADDED Requirements

### Requirement: Batch provenance and rollback

Every recipe apply SHALL allocate one readable sequential batch id (no hash-derived identifier), record the batch with its kind, item counts, and backup path in an additive ingest-batch registry, and stamp every content row it writes with that batch id. A whole-batch rollback SHALL run as one transaction that first writes a fresh recoverable backup, then deletes exactly the content rows carrying that batch id, and then marks the batch rolled back. Rollback SHALL refuse a batch whose content rows still have dependent learning records, and SHALL refuse an already rolled-back batch.

#### Scenario: Apply records the batch

- **WHEN** a gate-passed manifest is applied with `--apply`
- **THEN** one batch record with kind, item counts, and backup path exists in the registry and every inserted row carries the batch id

#### Scenario: Roll back a whole batch

- **WHEN** rollback is requested for a recorded batch whose rows have no dependent learning records
- **THEN** exactly the rows stamped with that batch id are removed in one transaction after a fresh backup, the registry marks the batch rolled back, and the reported accounting matches the recorded counts

#### Scenario: Rollback refuses dependent learning records

- **WHEN** any content row of the batch is referenced by an attempt, feedback event, schedule row, progress row, or learner signal
- **THEN** the rollback fails without deleting anything and names the blocking dependency

#### Scenario: Double rollback is refused

- **WHEN** rollback is requested for a batch already rolled back
- **THEN** the command fails without writing and reports the batch as already rolled back
