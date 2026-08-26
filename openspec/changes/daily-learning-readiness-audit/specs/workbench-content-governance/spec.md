## ADDED Requirements

### Requirement: Composable ingestion commands

The workbench SHALL expose `prepare`, `run`, `gate`, `apply`, `render`, and official `recipe` ingestion commands that exchange explicit UTF-8 artifacts. Preparing work SHALL NOT start an Agent, running Agent work SHALL require an explicit available provider with no fallback, and recipes SHALL perform no pool write unless the caller supplies `--apply`.

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

### Requirement: Independent formal-problem audit

A sourced formal problem SHALL have a non-empty solution produced during one Agent task and a complete independent audit produced in a fresh Agent session before formal apply. The audit SHALL cover source consistency, problem meaning, formatting, knowledge-point mapping, answer correctness, and solution completeness for every item, and every decision SHALL be PASS.

#### Scenario: Audit coverage is incomplete

- **WHEN** a solution batch omits an audit entry or required audit dimension for any problem
- **THEN** the formal-problem gate fails and identifies the uncovered problem

#### Scenario: An audit rejects one problem

- **WHEN** any independent audit decision is not PASS
- **THEN** the entire batch is ineligible for formal apply

### Requirement: Atomic formal-pool backfill

A formal-problem batch SHALL be applied in one transaction only after every item passes all gates. The operation SHALL create a recoverable database copy before changing the active pool, and any apply failure SHALL leave the active pool unchanged. The current pool SHALL NOT expose a partial solution backfill.

#### Scenario: One item fails before apply

- **WHEN** one of 303 solution records fails its gate
- **THEN** none of the 303 formal problem solutions changes in the active pool

#### Scenario: Apply a complete backfill

- **WHEN** all 303 solution and audit records pass and apply is explicitly requested
- **THEN** a recoverable copy is created and all formal solutions become visible after one committed transaction

#### Scenario: Apply transaction fails

- **WHEN** an error occurs while applying a qualified batch
- **THEN** the transaction rolls back and every original formal problem remains unchanged

### Requirement: Problem-source damage gate

The deterministic problem gate SHALL reject missing solutions, malformed or empty superscript/subscript tags, tags that split ordinary words, unknown raw HTML, and suspicious formula damage. Balanced non-empty `<sup>` and `<sub>` contents MAY pass for safe rendering after their contents are escaped; presentational difficulty stars SHALL NOT substitute for the Agent's semantic audit.

#### Scenario: Reject a broken OCR word

- **WHEN** a subscript tag interrupts an ordinary source word
- **THEN** the gate fails with the affected problem and markup reason

#### Scenario: Accept limited mathematical markup

- **WHEN** a problem contains balanced non-empty superscript or subscript markup without word splitting
- **THEN** the deterministic markup gate accepts that construct subject to the independent semantic audit

