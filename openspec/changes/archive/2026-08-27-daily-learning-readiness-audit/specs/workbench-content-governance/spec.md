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

The current recovery SHALL NOT weaken a rejected knowledge-point mapping to make the gate pass. Its corrective knowledge-point and mapping artifact SHALL be independently audited before it can join the formal apply.

#### Scenario: Audit coverage is incomplete

- **WHEN** a solution batch omits an audit entry or required audit dimension for any problem
- **THEN** the formal-problem gate fails and identifies the uncovered problem

#### Scenario: An audit rejects one problem

- **WHEN** any independent audit decision is not PASS
- **THEN** the entire batch is ineligible for formal apply

#### Scenario: A mapping requires a missing concept

- **WHEN** an independent audit rejects a formal-problem mapping because the required chapter concept is absent
- **THEN** an explicit knowledge-point and mapping correction must independently pass the same formal gate before the recovery becomes eligible for apply

### Requirement: Approved chapter mapping repair

The current chapter recovery SHALL create `dmath-ch06-kp-029` for 子集的位串生成, `dmath-ch06-kp-030` for 字典序 r-组合生成, and `dmath-ch06-kp-031` for 康托展开/排列对应. It SHALL repair exactly these thirteen formal-problem mappings: `067 -> 003,009,010`; `156 -> 009,010,012,013`; `189 -> 014,026`; `190 -> 014,026`; `280 -> 020`; `281 -> 003,020`; `294 -> 029`; `295 -> 030`; `297 -> 030`; and `300`, `301`, `302`, `303 -> 031`.

#### Scenario: Qualify the chapter mapping repair

- **WHEN** the three new knowledge points and thirteen final mappings have complete independent PASS decisions
- **THEN** they may join the 303 qualified solutions in the single formal-pool recovery transaction

#### Scenario: Keep the current pool unchanged before qualification

- **WHEN** any new knowledge point or repaired mapping lacks a complete PASS decision
- **THEN** the active pool retains its existing 28 knowledge points and original formal-problem mappings

### Requirement: Atomic formal-pool backfill

The current formal-pool recovery SHALL apply the 303 solutions, three approved knowledge points, and thirteen approved mapping repairs in one transaction only after every item passes all gates. The operation SHALL create one recoverable database copy before changing the active pool, and any apply failure SHALL leave the active pool unchanged. The current pool SHALL NOT expose a partial solution, knowledge-point, or mapping update.

#### Scenario: One item fails before apply

- **WHEN** any solution, new knowledge point, or repaired mapping fails its gate
- **THEN** the active pool retains all 303 empty solutions, 28 knowledge points, and original mappings

#### Scenario: Apply a complete backfill

- **WHEN** all 303 solutions, three new knowledge points, thirteen repaired mappings, and their independent audit records pass and apply is explicitly requested
- **THEN** one recoverable copy is created and one committed transaction makes all 303 solutions visible, preserves 303 formal problems, and yields 31 knowledge points with the qualified mappings

#### Scenario: Apply transaction fails

- **WHEN** an error occurs while applying a qualified batch
- **THEN** the transaction rolls back and all original solutions, knowledge points, and mappings remain unchanged

### Requirement: Problem-source damage gate

The deterministic problem gate SHALL reject missing solutions, malformed or empty superscript/subscript tags, tags that split ordinary words, unknown raw HTML, and suspicious formula damage. Balanced non-empty `<sup>` and `<sub>` contents MAY pass for safe rendering after their contents are escaped; presentational difficulty stars SHALL NOT substitute for the Agent's semantic audit.

#### Scenario: Reject a broken OCR word

- **WHEN** a subscript tag interrupts an ordinary source word
- **THEN** the gate fails with the affected problem and markup reason

#### Scenario: Accept limited mathematical markup

- **WHEN** a problem contains balanced non-empty superscript or subscript markup without word splitting
- **THEN** the deterministic markup gate accepts that construct subject to the independent semantic audit
