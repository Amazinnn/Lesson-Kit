## MODIFIED Requirements

### Requirement: Batch provenance and rollback

Every committed independent valid mutation unit SHALL retain readable batch provenance, affected counts and backup references. Cross-chapter input SHALL retain per-chapter provenance and original chapter resolution. Explicit undo of successfully applied batches SHALL be retired. Old batch and rolled-back records SHALL remain readable as historical facts. An unsupported old rollback request SHALL perform no write. Repair SHALL use ordinary direct content mutations.

#### Scenario: Apply records the batch

- **WHEN** a gate-passed manifest is applied with `--apply`
- **THEN** one batch record with kind, item counts, and backup path exists in the registry and every inserted row carries the batch id

#### Scenario: Roll back a whole batch

- **WHEN** a caller requests rollback of a previously successful batch
- **THEN** the retired operation performs no deletion and directs the caller to ordinary content repair

#### Scenario: Rollback refuses dependent learning records

- **WHEN** a rollback request names a batch with dependent learning records
- **THEN** the retired operation performs no write and the learning records remain

#### Scenario: Double rollback is refused

- **WHEN** a rollback request names a historically rolled-back batch
- **THEN** the retired operation performs no write and historical state remains readable

#### Scenario: One chapter is undone while the other stays

- **WHEN** a caller requests rollback of one chapter from an applied multi-chapter bundle
- **THEN** neither chapter is undone and direct scoped repair remains the supported operation

### Requirement: Atomic staged content bundle

A content-bundle SHALL accept new knowledge points, formal problems, micro quizzes, flash cards and required source figures as a staged or inline kind/type manifest. Every item SHALL resolve one valid chapter from its own value or the manifest value, never the active UI chapter. IDs, figure paths, quiz IDs and duplicate scope SHALL follow that chapter. Input SHALL be prevalidated into independent dependency-complete units. Each valid unit SHALL commit consistently with a recoverable backup and readable per-chapter batch provenance. Invalid items and dependent units SHALL remain unchanged while independent valid units complete. There SHALL be no fixed item or chapter ceiling. Successful-batch undo SHALL be unavailable.

#### Scenario: Missing knowledge point is included

- **WHEN** a source problem needs a new knowledge point included in the same bundle
- **THEN** both validate and commit together, or neither is written

#### Scenario: Required image is missing

- **WHEN** a problem depends on an unavailable or invalid source image while independent valid content is present
- **THEN** the problem and dependent unit remain unchanged while independent valid units complete

#### Scenario: Thirty valid exercises

- **WHEN** one bundle contains thirty valid exercises and their dependencies
- **THEN** all commit under one batch id

#### Scenario: One bundle imports two chapters

- **WHEN** a bundle carries chapter-12 and chapter-13 items in one manifest
- **THEN** every id carries its own chapter prefix, each figure lands under its own chapter directory, and the bundle records one batch for each chapter

#### Scenario: An item cannot be assigned to a chapter

- **WHEN** one item lacks both item and manifest chapter while independent valid items have chapters
- **THEN** the item is refused with its label and its dependency unit stays unchanged while independent units complete

#### Scenario: A declared chapter is not an identifier

- **WHEN** an item or the manifest declares an invalid chapter identifier
- **THEN** the affected unit is refused and no invalid-chapter content is written while independent valid units can complete

#### Scenario: An inline bundle carries the same contract

- **WHEN** a manifest arrives inline instead of as a staged file
- **THEN** the same chapter resolution, dependency grouping, provenance, backup and consistent-unit rules apply

### Requirement: In-place problem patch

Existing problems SHALL be edited without changing their readable identity or deleting learning history. Single and bulk problem-patch operations SHALL reject unknown IDs, unsupported fields, cross-course IDs, ID changes and difficulty commands in this payload. Bulk patches SHALL prevalidate all items, report itemized results and commit independent valid units with batch provenance and recoverable backup. Invalid units SHALL retain prior state. Practice-mode and micro-quiz validation SHALL cover touched fields and SHALL NOT reject untouched legacy fields. Explicit successful-batch undo SHALL be retired, and corrected retries SHALL not duplicate applied events.

#### Scenario: One problem is edited explicitly

- **WHEN** the learner or the Agent patches one existing problem with new attributes
- **THEN** exactly that row changes in one transaction, its id and its learning records are untouched, and the result reports the written fields

#### Scenario: A bulk patch is all or nothing

- **WHEN** a bulk patch mixes valid independent items with an unknown ID, unknown field or invalid value
- **THEN** valid independent units commit and invalid units remain unchanged with itemized outcomes

#### Scenario: A patch is rolled back value for value

- **WHEN** a caller requests explicit undo of an applied patch
- **THEN** no successful patch is undone and ordinary direct repair remains available

#### Scenario: Unsupported fields are refused

- **WHEN** a patch payload carries a field the pool does not manage, or a difficulty field
- **THEN** it is refused with the writable field list (or the `lesson-kit difficulty` pointer) and nothing is written

### Requirement: Composable ingestion commands

The workbench SHALL expose `prepare`, `run`, `gate`, `apply`, `render`, official `recipe`, ingestion commands that exchange explicit UTF-8 artifacts. Preparing work SHALL NOT start an Agent, running Agent work SHALL require an explicit available provider with no fallback, recipes SHALL perform no pool write unless the caller supplies `--apply`. Explicit successful-batch rollback SHALL be retired.

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
- **THEN** the retired command performs no write and reports ordinary content repair as the available operation
### Requirement: Ingest batch registry visibility

The workbench SHALL expose a read-only CLI listing of recorded ingest
batches (`ingest batches`), reporting for each batch its id, kind, item
counts, applied timestamp, rollback state, and backup path, newest first.
The listing SHALL perform zero writes and SHALL NOT require any prior
artifact, so that agents and the owner can inspect provenance and historical state. Explicit successful-batch undo SHALL remain retired.

#### Scenario: List recorded batches

- **WHEN** a caller runs the batch listing after two applies, one of them
  rolled back
- **THEN** both batches are reported newest first with their kind, counts,
  and rollback state, and the rolled-back batch is marked as such

#### Scenario: Listing performs zero writes

- **WHEN** the batch listing runs over any pool
- **THEN** database contents and row counts remain identical before and after
### Requirement: Content identity dedup at ingest

Content that is the same problem as an item already in the pool, or as an item
earlier in the same manifest, SHALL be refused rather than stored a second
time. The gate SHALL derive a normalized content identity from the problem
text — case folded, whitespace collapsed, punctuation dropped, math delimiters
and rendering variants canonicalized, and export noise such as score, author,
and unit lines removed — and SHALL NOT truncate it, because a truncated key
cannot separate a duplicate from a similar item that diverges later in the
stem. Two items whose identities match SHALL be a duplicate regardless of their
keys, their source files, or their chapters, and the refusal SHALL name the
colliding problem id together with its source evidence so the caller can see
which row already covers the content. Two stems that differ beyond those
variants SHALL NOT collide: similar-but-different items are deliberately kept.
A duplicate refusal SHALL isolate the invalid dependency unit, report each collision and allow independent valid units to commit without inserting duplicate content.

#### Scenario: The same item arrives from a second source file

- **WHEN** a manifest item's normalized identity equals an existing problem's identity in the same course scope
- **THEN** the gate refuses that item with a reason naming the existing problem id and the invalid unit is unchanged while independent valid units can complete

#### Scenario: The same item appears twice in one manifest

- **WHEN** two items of one manifest share a normalized identity
- **THEN** the gate reports an itemized reason for each and the colliding units remain unchanged while independent valid units can complete

#### Scenario: Rendering variants still collide

- **WHEN** an item and an existing problem differ only in whitespace, punctuation, `$…$` rendering, or export noise
- **THEN** they are treated as the same problem and the second one is refused

#### Scenario: Similar items are kept

- **WHEN** two stems differ beyond the normalized variants
- **THEN** both are accepted, and neither is reported as a duplicate

#### Scenario: A duplicate never half-writes

- **WHEN** a manifest mixes a duplicate with otherwise valid new items
- **THEN** the duplicate is reported and the duplicate unit remains unchanged while independent valid new items reach the pool
