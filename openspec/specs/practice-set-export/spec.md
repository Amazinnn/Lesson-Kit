# practice-set-export Specification

## Purpose

Compose and export one **Paper**, the smallest executable answering unit in
Lesson Kit. A Paper freezes an ordered set of items before a Practice Run begins.
The existing `pull` command remains the deterministic assembly engine and the
legacy manifest wire kind remains `practice-set` for compatibility, but those
names do not define a user-facing Practice Set: a product Practice Set is a
container that may organize multiple Papers and is not itself executed.

This specification covers Paper assembly, reproducible manifests, rendered
student/solution sheets, zero-write validation, and managed saved Papers.
## Requirements
### Requirement: Paper assembly

One `pull` invocation SHALL assemble a Paper from any combination of a
knowledge-point scope (explicit knowledge points, else the active chapter lens),
conditional filters (source kind, origin kind, source group, exam year, and the
objective difficulty range), learner-driven selection (weak knowledge points,
due problems, and previously wrong problems), and exact problem ids supplied by
an Agent or another authoring workflow. Conditional filters SHALL restrict the
candidate set only. Exact problem ids are an **authoring primitive**: they MAY be
used by the Agent/CLI to make a deterministic Paper, but SHALL NOT create a
browser affordance for the learner to hand-pick individual questions into an
active Practice Run. Every selected problem SHALL report why it entered the
Paper — `scope`, `weak`, `due`, `wrong`, or `explicit` — and unfilled
knowledge-point demand SHALL remain reported as a shortage instead of being
filled with invented content. Assembling a Paper SHALL perform zero learning
writes.

#### Scenario: Assemble by scope and filters

- **WHEN** the Agent assembles a Paper for one chapter restricted to textbook final-exam problems of one exam year
- **THEN** only problems matching every condition are returned, each carrying its reason

#### Scenario: Agent pins one exact problem while authoring

- **WHEN** the Agent names one exact problem id while assembling a Paper
- **THEN** that problem may be pinned in the Paper with reason `explicit`, without creating a learner-facing manual-pick control or starting a Practice Run

#### Scenario: Assemble from wrong problems

- **WHEN** the Agent assembles a Paper from previously wrong problems
- **THEN** the Paper contains the problems whose progress or latest attempt marks them wrong, each with reason `wrong`

#### Scenario: Shortage stays honest

- **WHEN** the scope holds fewer problems than requested
- **THEN** the result reports the shortage per knowledge point and no problem is invented

### Requirement: Paper manifest

A Paper manifest SHALL be UTF-8 JSON carrying the Paper title, the ordered
problem ids with their reasons, and the assembly inputs needed to reproduce the
selection. It SHALL be validated before use — every named problem SHALL exist
and no problem SHALL repeat — and reading a manifest SHALL perform zero writes.
Re-running the same manifest SHALL reproduce the same ordered Paper.

For compatibility with existing files and commands, the manifest's wire-level
`kind` SHALL remain `practice-set` in v1. That compatibility token SHALL NOT be
used to infer that the product-level Practice Set is directly executable.

#### Scenario: Manifest round-trip

- **WHEN** an assembled Paper is written as a manifest and read back
- **THEN** the same ordered problems are selected again and no learning row changes

#### Scenario: Invalid manifest is refused

- **WHEN** a manifest names an unknown problem or names one twice
- **THEN** the command exits nonzero, names the offending problem, and writes nothing

### Requirement: Rendered Paper and solutions

The CLI SHALL render one Paper into two files: a student sheet and its solution
file, sharing continuous numbering. The student file SHALL contain problem text
only — no answer, no solution, and none of `problem_id`, `kp_id`, or
`source_kind`. The solution file SHALL mirror the numbering exactly and SHALL
write `待补` for a problem whose solution is not stored. Rendering SHALL be
deterministic, and figure references SHALL remain the stored relative references
rather than copied bytes. A single-chapter Paper SHALL default to the documented
problem-set artifact paths, and a Paper spanning chapters SHALL be placeable in
a caller-chosen directory and base name.

#### Scenario: Print a single-chapter Paper

- **WHEN** the Agent prints an assembled chapter Paper with default paths
- **THEN** the two files appear at the documented output paths, the student file leaks no answer or internal identifier, and both files number identically

#### Scenario: Print a Paper spanning chapters

- **WHEN** the Agent prints a Paper spanning several chapters into a chosen directory and base name
- **THEN** the two files use that directory and base name and the numbering still matches

#### Scenario: Missing solution

- **WHEN** a selected problem has no stored solution
- **THEN** the solution file writes `待补` at that number and the student file is unaffected

### Requirement: Zero-write Paper check

`pull <workspace> check --input <file|->` SHALL validate a Paper manifest and
preview the rendered Paper without writing anything. It SHALL report the
selected count, the shortage per knowledge point, the problems without a stored
solution, duplicate or unknown problems, and any answer or internal identifier
that would leak into the student sheet. Failures SHALL be itemized and SHALL
exit nonzero.

#### Scenario: Check writes nothing

- **WHEN** the Agent checks a valid Paper manifest
- **THEN** the report lists the selected problems and their gaps and neither a learning row nor a rendered file is written

#### Scenario: Leakage is caught

- **WHEN** a Paper would place an answer or an internal identifier into the student sheet
- **THEN** the check fails and names the offending item

### Requirement: Managed saved Paper

The system SHALL expose `lesson-kit papers <workspace> save --input <manifest>`
to save an existing Paper manifest using the same managed store as the browser.
It SHALL preserve the ordered problem IDs and request metadata, validate the
manifest before saving, and reject a supplied course that differs from the
selected workspace course. It SHALL leave SQLite learning state, the source
manifest and existing saved Papers unchanged.

The current storage directory, `ps-NNN` identifiers, and `/practice-sets/...`
compatibility routes MAY remain during v1 migration. They are implementation
compatibility names for saved Papers, not the product definition of Practice Set.
A Practice Run started from such a saved record SHALL execute the frozen Paper
items and persist `source_kind = paper` in new execution state/history.

#### Scenario: Save a valid assembled Paper

- **WHEN** the caller saves a valid manifest containing existing unique ordered problem IDs
- **THEN** the command exits 0 and returns JSON containing the persisted compatibility id, title, count and workspace-relative Paper page URL
- **AND** the saved Paper is readable through the existing browser Paper list and retains the same problem order and request metadata

#### Scenario: Reject an invalid or cross-course manifest

- **WHEN** the input is unreadable or malformed, violates the existing Paper manifest contract, references unknown or duplicate IDs, lacks a valid title/request, or declares a different course
- **THEN** the command exits 2 with a JSON error and creates no saved Paper or database changes

### Requirement: Agent distinguishes exported and managed Papers

The Agent practice contract SHALL distinguish `pull --plan`/`--print` exports
from managed saved Papers. When the learner requests saving a Paper or making it
available in Workbench, the contract SHALL direct the Agent to the managed-save
command and require a successful receipt before reporting success. Export-only
requests SHALL remain supported.

#### Scenario: Report a successful managed save

- **WHEN** managed saving succeeds
- **THEN** the Agent can report the saved title, count and returned page link without representing a job artifact as the saved Paper

#### Scenario: Export alone does not prove saving

- **WHEN** only a job manifest or printed sheet exists, or managed saving fails
- **THEN** the contract prohibits claiming that the Paper is saved in the Workbench list

### Requirement: Paper is the Practice Run boundary

A Practice Run SHALL execute a frozen Paper, never a live knowledge-point query.
Knowledge points, learner evidence, filters, and Agent instructions MAY constrain
Paper assembly, but once execution begins they SHALL NOT silently add, remove, or
replace items in that run. Historical callers that label assembly origin as
`quick`, `practice_set`, or `agent` MAY be accepted during migration; every newly
persisted active execution and run archive SHALL normalize that origin to
`paper`. Replaying a historical run SHALL likewise create a new Paper-sourced
execution from the archived fixed items.

#### Scenario: Knowledge-point entry assembles before execution

- **WHEN** the learner chooses to practice one knowledge point
- **THEN** that knowledge point constrains Paper assembly, and the Practice Run begins only after the Paper's item list is fixed

#### Scenario: Old quick caller is normalized

- **WHEN** a compatibility caller submits a fixed item list labelled `quick`
- **THEN** the new active execution stores `source_kind = paper` and does not preserve `quick` as a peer execution type

#### Scenario: Replaying old history upgrades the execution source

- **WHEN** an archived run created under `quick`, `practice_set`, or `agent` is replayed
- **THEN** the exact archived items are reused and the new execution stores `source_kind = paper`

### Requirement: Saved Paper updates preserve container identity
An update explicitly targeting an existing Paper SHALL retain its Paper ID. Effective title/description-only or no-op changes SHALL retain unfinished execution progress. A manual change to item membership or order SHALL first report its exact progress impact and require confirmation, then reset only that Paper's unfinished progress/drafts without modifying questions, historical attempts, ratings or other Papers. Cancellation SHALL leave both content and progress unchanged. Saving SHALL NOT automatically start practice.

#### Scenario: Update the original Paper instead of creating another
- **WHEN** the caller confirms a membership/order update of a partially practiced saved Paper
- **THEN** the same Paper ID contains the new ordered items and its unfinished progress is reset, while learning evidence and other Papers remain unchanged

#### Scenario: Rename without resetting practice
- **WHEN** only a saved Paper's title or description changes
- **THEN** its unfinished state, drafts and item order remain unchanged

#### Scenario: Cancel a structure change
- **WHEN** the user rejects the displayed progress-reset impact
- **THEN** neither the Paper nor any execution or learning record changes

### Requirement: Saved container management does not depend on live item availability
The system SHALL keep saved Paper metadata visible, inspectable, repairable and deletable even when an item is missing. It SHALL report missing item identities explicitly and SHALL NOT silently omit the container from its list. Starting an invalid or empty Paper SHALL fail clearly without starting an execution or writing learning state. Deleting a Paper SHALL remove only its container and unfinished progress/drafts, preserving questions, learning evidence and historical runs with the deleted source identity/label.

#### Scenario: Repair an orphaned Paper
- **WHEN** an existing Paper references missing questions and an author explicitly supplies a valid replacement item list
- **THEN** the original container can be repaired under the confirmed update rules instead of requiring delete/re-import

#### Scenario: Delete a container whose question is missing
- **WHEN** the learner confirms deleting a saved Paper containing an unavailable question
- **THEN** the container and its unfinished state are removed without deleting any surviving question, attempt, rating or historical run

#### Scenario: Last question was removed
- **WHEN** deletion of a question leaves a saved Paper with no items
- **THEN** the empty container remains visible and manageable, and starting it is refused without learning writes

### Requirement: Corrected imports identify existing update targets explicitly
The authoring workflow SHALL distinguish creation from correction of existing Paper/question IDs. A correction SHALL use explicit existing identities and SHALL NOT infer overwrite identity from a matching title, similar question text or an answering-type prefix. Correcting a question to an objective form SHALL NOT allocate a replacement ID merely because its content type changes.

#### Scenario: Correct an existing open-form import
- **WHEN** an author explicitly targets an existing question to correct its choices or answering type
- **THEN** the existing question ID remains and existing Paper membership/order is unchanged
