# workbench-content-governance Specification

## Purpose

Set the single boundary through which pool content may change: explicit
create/update/delete/state/gate/promote commands, issued by the student or an
Agent acting on an explicit request. Everything else — browsing, drafts,
ordinary conversation — is read-only. Mutations are transactional and physical
(no tombstones), current-state replacement stays event-noise-free, ingestion
and backfill run as composable audited commands, and a source-damage gate
keeps broken upstream material out of the formal pool.
## Requirements
### Requirement: Explicit content mutation boundary

Pool content SHALL change only after an explicit create, update, delete, or
state command, or through the structured check ingest action defined by the
ai-teacher-bridge capability. Browsing, search, navigation, draft text,
ordinary Agent conversation, and provider tool events SHALL NOT mutate pool or
learning data. After a successful Agent mutation, the teacher answer SHALL expose a concise object, action, and workbench-link summary rather than raw commands, SQL, or tool logs.

#### Scenario: Discuss a possible edit

- **WHEN** the learner discusses changing a knowledge point without explicitly asking to apply the change
- **THEN** the Agent may explain or propose the edit but no data command is issued

#### Scenario: Apply an explicit edit

- **WHEN** the learner explicitly requests a content change and the Agent completes it
- **THEN** the answer identifies the changed object and action with a workbench link and omits internal command logs

#### Scenario: Apply content through the bridge check action

- **WHEN** the learner explicitly asks in an Agent conversation to add pool content and the reply carries a valid check ingest action
- **THEN** the pool changes only through the same deterministic gate and batch-recorded apply as the CLI recipes

### Requirement: Transactional physical deletion

Content deletion SHALL be physical and atomic, with no tombstone or deletion log. Deleting a problem SHALL remove its current state, schedule, signals, attempts, progress, and feedback. Deleting a knowledge point SHALL remove its relations and membership from multi-owned problems, and SHALL delete any newly ownerless problem with the same cascade. Deleting a relation SHALL remove only that relation.

#### Scenario: Delete a problem with learning records

- **WHEN** a formal problem is explicitly deleted
- **THEN** the problem and every dependent learning row are absent after one committed transaction

#### Scenario: Delete a knowledge point with shared and ownerless problems

- **WHEN** a knowledge point owns both a shared problem and a sole-owned problem
- **THEN** the shared problem remains without that membership, the sole-owned problem and its dependent rows are deleted, and all attached relations are removed atomically

#### Scenario: A deletion step fails

- **WHEN** any statement in a content deletion transaction fails
- **THEN** the entire deletion is rolled back and the original content remains

### Requirement: Current-state replacement without event noise

An explicit `state` command SHALL replace the current knowledge-point or problem state and update its schedule through the existing equivalent rating. It SHALL NOT append a feedback event, learner signal, or conversation-side learning log.

#### Scenario: Replace state through Agent data

- **WHEN** the Agent explicitly sets an item to `mastered`
- **THEN** current state and schedule reflect rating 5 while feedback and signal counts remain unchanged

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

### Requirement: Batch provenance and rollback

Every recipe apply SHALL allocate one readable sequential batch id (no hash-derived identifier), record the batch with its kind, item counts, and backup path in an additive ingest-batch registry, and stamp every content row it writes with that batch id. A bundle that spans chapters SHALL record one batch per chapter, each stamped on that chapter's rows, so a whole-batch rollback undoes one chapter without touching its siblings. A whole-batch rollback SHALL run as one transaction that first writes a fresh recoverable backup, then deletes exactly the content rows carrying that batch id, and then marks the batch rolled back. Rollback SHALL refuse a batch whose content rows still have dependent learning records, and SHALL refuse an already rolled-back batch.

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

#### Scenario: One chapter is undone while the other stays

- **WHEN** a two-chapter bundle was applied and rollback is requested for one of its two batches
- **THEN** only that chapter's rows and its now-unreferenced figures are removed, the sibling batch and its rows stay, and the registry shows one batch rolled back and one still applied

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

### Requirement: Ingest stays inside one course

An ingest batch SHALL belong to exactly one course: the course of the workspace's
pool. Content ids in a `micro-quiz-patch` or `flash-card-patch` manifest SHALL
carry that course prefix, and a batch whose ids carry another course SHALL be
refused by the gate with an itemized reason naming the expected prefix. A
`figure-patch` manifest SHALL name the workspace's own course and a chapter that
is a plain identifier, and its figure paths SHALL resolve inside the workspace's
`.lessonkit/figures/<course>/<chapter>/` directory; a manifest whose course or
chapter would leave that directory SHALL be refused and no file SHALL be written.

#### Scenario: A foreign-course id is refused

- **WHEN** a micro-quiz or flash-card manifest carries ids prefixed by a course other than the workspace's
- **THEN** the gate fails with an itemized reason naming the expected prefix and nothing is written

#### Scenario: A figure patch cannot leave its course folder

- **WHEN** a figure-patch manifest names a course other than the workspace's, or a chapter containing a path separator or `..`
- **THEN** the gate fails and no figure file is written outside `.lessonkit/figures/<workspace course>/<chapter>/`

#### Scenario: Same-course content still applies

- **WHEN** a manifest carries the workspace's own course prefix and a valid chapter
- **THEN** the batch passes the same deterministic gates as before and applies as one recorded batch

#### Scenario: A batch with no active course is refused

- **WHEN** a manifest is applied to a workspace whose registry entry has no active course
- **THEN** the gate fails with an explicit reason instead of guessing a prefix

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

### Requirement: Requested problem type and source form are preserved

Micro Quiz SHALL remain a supported problem type with yes/no, single-choice,
and multiple-choice subtypes, and the existing four practice entries SHALL
remain available. Importing textbook exercises SHALL preserve each source
problem's wording, numerical conditions, answer form, and problem type. A
source exercise SHALL use `origin_kind=source_problem`; it SHALL become a micro
quiz only when the source is already that type or the learner explicitly asks
for a micro adaptation. Generated simple choice/judgement questions remain
allowed with `origin_kind=generated_grounded`.

#### Scenario: Import a textbook proof

- **WHEN** a learner asks to import a textbook proof exercise without requesting adaptation
- **THEN** a formal source problem is created and no choice options are invented

#### Scenario: Explicit micro adaptation

- **WHEN** the learner asks to convert source material into a single-choice micro quiz
- **THEN** an adapted micro problem may be created with a valid structured subtype

#### Scenario: Existing micro flow remains compatible

- **WHEN** a valid micro problem is pulled through the existing small-quiz or yes/no entry
- **THEN** its current structured answering and feedback behavior remains available

### Requirement: Atomic staged content bundle

A `content-bundle` SHALL contain one or more new knowledge points, formal
problems, micro quizzes, flash cards, and required source figures. Its manifest
SHALL be staged under the owning conversation, or carried inline when it declares
its `kind` or its `type` as `content-bundle`. Every knowledge point, problem,
and flash card SHALL resolve exactly one chapter: an item MAY declare its own
`chapter`, otherwise the bundle-level `chapter` applies; an item that resolves no
chapter SHALL be refused with its label and nothing SHALL be written, and the
workspace's active chapter SHALL NOT be used as a fallback, so a manifest that
spans chapters can never be silently assigned to the chapter the learner happens
to be viewing. A single bundle MAY therefore span several chapters, and every
derived value SHALL follow its item's chapter — allocated id prefix, figure
logical path and destination directory, micro-quiz id, and the duplicate check.
The complete bundle SHALL be prevalidated and applied under one backup and one
transaction; any invalid entity, reference, or file SHALL leave both SQLite and
the figure destination unchanged. It SHALL record one batch per chapter present,
in chapter order, so each chapter's content can be rolled back on its own. There
SHALL be no fixed ceiling on items or on chapters per bundle.

#### Scenario: Missing knowledge point is included

- **WHEN** a source problem needs a new knowledge point included in the same bundle
- **THEN** both validate and commit together, or neither is written

#### Scenario: Required image is missing

- **WHEN** a problem depends on an unavailable or invalid source image
- **THEN** the complete bundle fails and the incomplete problem is not inserted

#### Scenario: Thirty valid exercises

- **WHEN** one bundle contains thirty valid exercises and their dependencies
- **THEN** all commit under one batch id

#### Scenario: One bundle imports two chapters

- **WHEN** a bundle carries chapter-12 and chapter-13 items in one manifest
- **THEN** every id carries its own chapter prefix, each figure lands under its own chapter directory, and the bundle records one batch for each chapter

#### Scenario: An item cannot be assigned to a chapter

- **WHEN** a bundle has no chapter of its own and an item declares none, even though the workspace has an active chapter
- **THEN** that item is refused with its label and no content and no figure is written

#### Scenario: A declared chapter is not an identifier

- **WHEN** an item or the bundle declares a chapter that is not a lowercase ASCII identifier
- **THEN** the bundle is refused with that reason and nothing is written

#### Scenario: An inline bundle carries the same contract

- **WHEN** the manifest arrives inline in the reply instead of as a staged file
- **THEN** the same chapter resolution, per-chapter batches, backup, and transaction apply

### Requirement: Source and solution provenance

Every new Agent-managed problem SHALL store non-empty source evidence visible
to the learner. OCR errors MAY be corrected by checking the original page, but
the content SHALL NOT otherwise change the source wording, values, options, or
answer form. A source-provided short answer SHALL be stored separately from a
detailed solution. A source solution SHALL be identified as source material;
an on-demand AI explanation SHALL be identified as generated and MAY enter
without an independent semantic audit. Legacy rows MAY leave these fields null.

#### Scenario: Textbook supplies only a short answer

- **WHEN** an exercise has a source answer but no detailed solution
- **THEN** the source answer is preserved and no AI explanation is generated until requested

#### Scenario: Learner requests an explanation

- **WHEN** an AI explanation is generated on request
- **THEN** it is stored and displayed as `AI 生成解析` without overwriting the source answer

### Requirement: Completeness remains advisory

The system SHALL NOT add a deterministic source-coverage gate in this change.
An Agent MAY describe an import as complete in prose, but product/developer
documentation SHALL state that this claim is advisory and may omit source
items.

#### Scenario: Agent claims all items were imported

- **WHEN** the Agent reports completion
- **THEN** no hidden mechanical guarantee of source coverage is implied

### Requirement: In-place problem patch

Content that already exists SHALL be changeable without deleting and
re-importing it, because a problem's readable id is its identity and every
attempt, rating, and schedule hangs off it. A patch SHALL name existing problems
only, SHALL refuse unknown ids, unknown field names, an id outside the
workspace's course, and any attempt to change the id, and SHALL keep difficulty
ratings a separate command. It SHALL be available as one explicit command per
problem and as one bulk manifest (`problem-patch`) that prevalidates every item,
records one readable batch id with the manifest snapshot **and each row's
previous values**, writes one recoverable backup, and applies in one
transaction: any invalid item leaves the pool untouched. Rolling such a batch
back SHALL restore the previous values instead of deleting rows, so the
learner's records survive an edit and its reversal. A patch SHALL resolve the
practice mode from the payload unless the caller declares it, SHALL validate the
resulting row against the micro-quiz contract for the parts it touches, and
SHALL NOT re-validate untouched legacy fields. Unknown field names SHALL be an
error rather than a silent drop.

#### Scenario: One problem is edited explicitly

- **WHEN** the learner or the Agent patches one existing problem with new attributes
- **THEN** exactly that row changes in one transaction, its id and its learning records are untouched, and the result reports the written fields

#### Scenario: A bulk patch is all or nothing

- **WHEN** a `problem-patch` manifest mixes valid items with an unknown id, an unknown field, or a contract violation
- **THEN** every reason is reported per item and no row, batch record, or backup changes state

#### Scenario: A patch is rolled back value for value

- **WHEN** an applied `problem-patch` batch is rolled back
- **THEN** every touched column returns to exactly its previous value, including cleared difficulty ratings, and the rows themselves remain

#### Scenario: Unsupported fields are refused

- **WHEN** a patch payload carries a field the pool does not manage, or a difficulty field
- **THEN** it is refused with the writable field list (or the `lesson-kit difficulty` pointer) and nothing is written

