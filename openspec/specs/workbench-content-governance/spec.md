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
A duplicate refusal SHALL follow the existing all-or-nothing rule — every reason
reported per item, nothing written, no batch recorded.

#### Scenario: The same item arrives from a second source file

- **WHEN** a manifest item's normalized identity equals an existing problem's identity in the same course scope
- **THEN** the gate refuses that item with a reason naming the existing problem id and nothing is written

#### Scenario: The same item appears twice in one manifest

- **WHEN** two items of one manifest share a normalized identity
- **THEN** the gate reports an itemized reason for each and the manifest is not applied

#### Scenario: Rendering variants still collide

- **WHEN** an item and an existing problem differ only in whitespace, punctuation, `$…$` rendering, or export noise
- **THEN** they are treated as the same problem and the second one is refused

#### Scenario: Similar items are kept

- **WHEN** two stems differ beyond the normalized variants
- **THEN** both are accepted, and neither is reported as a duplicate

#### Scenario: A duplicate never half-writes

- **WHEN** a manifest mixes a duplicate with otherwise valid new items
- **THEN** the duplicate is reported and no item of that manifest reaches the pool

### Requirement: Read-only pool content audit

The workbench SHALL provide a read-only audit over the workspace's pool that
reports content-hygiene findings for the selected scope: duplicate content
groups with their identity and member problem ids; fragment rows (a row whose
text is the continuation of another row, such as a stem that begins with a
connective or a row holding only an option label); objective items that carry
no practice mode; problems without a display title; figure references that do
not resolve to a file; and figure files that no item references. The audit
SHALL write nothing, SHALL be machine-readable, and SHALL exit non-zero when a
requested check reports findings, so a repair pass and a later regression check
can be gated on it.

#### Scenario: A pool with findings is reported

- **WHEN** the audit runs over a pool holding a duplicate group and an objective item without a practice mode
- **THEN** both findings are reported with their problem ids and the command exits non-zero

#### Scenario: A clean pool reports nothing

- **WHEN** the audit runs over a pool with no findings for the selected checks
- **THEN** it reports an empty finding set and exits zero

#### Scenario: The audit changes nothing

- **WHEN** the audit runs over any pool
- **THEN** row counts, row contents, and the recorded batch list are identical before and after

#### Scenario: The audit sizes and verifies a repair

- **WHEN** the audit runs with all checks before a content repair, and again after
- **THEN** its findings can be grouped by chapter and defect class both times, so the repair can be planned from the first run and verified against the second

### Requirement: Remove retired problem labels from current schemas

Workbench schema ensure SHALL physically remove an existing
`problems.topic_label` column, and a rebuilt problem table SHALL omit that
column. This requirement explicitly supersedes the previous ordinary-ensure
retention semantics introduced after PR106. Current databases SHALL NOT retain
problem labels in a hidden column or replacement table. Recovery backups MAY
preserve historical labels outside the migrated database.

The removal SHALL preserve every other current problem field and value,
learning row, foreign key and unrelated schema object. Existing legacy
provenance/difficulty upgrades remain governed by their existing requirements.
Problem manifests, patches, search and presentation SHALL continue to exclude
`topic_label`. The independent `flash_cards.topic_label` field and all its
existing values SHALL remain unchanged.

The explicitly authorized migration of registered course databases SHALL create
and prove recovery from an external SQLite backup before live deletion. The
observed c05 `problems_by_chapter` view SHALL omit only its `p.topic_label`
projection before the column drop, preserving its other SQL and columns.
Any other dependency on the target column SHALL block deletion and be reported.

#### Scenario: Open a current pool with historical problem labels

- **WHEN** schema ensure runs on a current pool with populated problem labels
- **THEN** `problems.topic_label` is absent from the resulting table
- **AND** all nontarget problem values, learning rows and flash-card labels are unchanged

#### Scenario: Rebuild a compatible legacy problem table

- **WHEN** schema ensure upgrades a compatible legacy problem table carrying labels
- **THEN** the rebuilt problem schema omits `topic_label`
- **AND** existing nontarget values and learning rows survive the upgrade

#### Scenario: Repeat schema ensure

- **WHEN** schema ensure runs again after removal
- **THEN** the problem label column is not reintroduced and no further schema change is reported

#### Scenario: Recover a database before live removal

- **WHEN** the operator prepares a registered course database for deletion
- **THEN** a separate SQLite backup and recovered copy prove that historical
  labels and all other data can be recovered before the live change

#### Scenario: A view references the retired column

- **WHEN** the registered c05 pool contains the observed `problems_by_chapter`
  view with a direct `p.topic_label` projection
- **THEN** the operator removes only that projection before dropping the column
- **AND** any additional dependency stops the migration for explicit review

### Requirement: Knowledge-point body paragraph typesetting check

A knowledge point's `body` is read as a sequence of paragraphs, where a
paragraph is a run of text between blank lines. A paragraph's **visible
characters** are what remain after inline math (`$$…$$`, `$…$`) and backticked
code are removed for the purpose of counting; nothing else is removed, and the
text itself is never altered.

A typesetting check SHALL report a knowledge point when any of its `body`
paragraphs falls outside the band **40 to 300 visible characters**, and SHALL
report each such knowledge point once, naming the number of paragraphs past
each bound together with the longest and shortest measured paragraph.

The check is read-only and advisory:

- it SHALL write nothing and SHALL NOT refuse, reject, or exit non-zero because
  of a typesetting finding;
- it SHALL NOT modify, normalize, reflow, split, trim, or reorder any text;
- it SHALL NOT state a preferred typesetting — no target paragraph length, no
  recommended section vocabulary, no suggested split point, no template;
- it SHALL report measured facts only, each recomputable from the stored text.

A paragraph whose visible character count is zero — a paragraph consisting only
of inline math or only of code — SHALL NOT count as too short. The band
applies to `body` only; `fragile` and `learning_action` are excluded because a
reminder note and an action line are written as short units by design.

The check SHALL be available at two points, sharing one measurement rule and one
report wording: over the content bundle before it is applied, and over the pool
after it is applied. Where no bundle is available to check, the check SHALL say
so in the report rather than reporting nothing, so that a caller can tell "checked
and clean" from "nothing to check".

#### Scenario: A body holding an over-long paragraph is reported with its measurement

- **WHEN** a knowledge point's body holds a paragraph of 1750 visible characters
- **THEN** the report names the knowledge point with one paragraph past the upper bound and the longest measured paragraph, and the run completes as it would for a clean pool

#### Scenario: A body holding a too-short paragraph is reported separately

- **WHEN** a knowledge point's body holds a paragraph of 12 visible characters
- **THEN** the report names the knowledge point under the short-paragraph section with its measured length, and the run completes as it would for a clean pool

#### Scenario: A paragraph of only math or only code is not a short paragraph

- **WHEN** a knowledge point's body holds a paragraph whose entire content is a display formula or a code block, leaving zero visible characters
- **THEN** that paragraph is not counted as too short

#### Scenario: A body violating both bounds appears once

- **WHEN** one knowledge point's body holds both an over-long and a too-short paragraph
- **THEN** it appears once in the over-long section, which comes first, and the row states how many paragraphs are past each bound

#### Scenario: A body inside the band is not reported

- **WHEN** a knowledge point's body holds only paragraphs between 40 and 300 visible characters
- **THEN** it is absent from both sections

#### Scenario: The check states no preferred typesetting

- **WHEN** the check reports any finding
- **THEN** the report contains no target length, no recommended section names, and no suggested split point, and every number in it is recomputable from the stored text

#### Scenario: The check changes nothing

- **WHEN** the check runs over a pool or a content bundle
- **THEN** row counts, row contents, and the recorded batch list are identical before and after

#### Scenario: Nothing to check is stated rather than implied

- **WHEN** the pre-apply check runs over a scope that has no content bundle
- **THEN** the report says that scope had nothing to check, which is distinguishable from a scope that was checked and found clean

