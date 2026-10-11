## ADDED Requirements

### Requirement: Version-controlled figure assets

The authored-content repository SHALL support binary figure assets under
`figures/<course-id>/...` in addition to the JSON authored-content projection.
The pool's `knowledge_points.figure_paths` and `problems.figure_paths` SHALL
remain the authority for which logical figures belong to authored content. Image
bytes SHALL NOT be stored in SQLite or embedded in JSON entity envelopes.

#### Scenario: A referenced problem figure is versioned

- **GIVEN** a problem references `dmath/ch06/example.png`
- **WHEN** figure assets are pushed to the authored-content repository
- **THEN** the exact bytes are written to `figures/dmath/ch06/example.png`
- **AND** the problem row and its logical path are unchanged

#### Scenario: One figure is shared by several owners

- **GIVEN** several authored objects reference the same logical figure path
- **WHEN** figure synchronization is planned or applied
- **THEN** the asset is handled once and the report identifies every owner

### Requirement: Figure synchronization is explicitly directional

Figure synchronization SHALL require an explicit `check`, `push`, or `pull`
direction. `check` and every dry run SHALL perform no file write. A differing
binary asset SHALL NOT acquire an automatic winner: only explicit push or pull
may overwrite the opposite side.

#### Scenario: Compare differing figure bytes

- **GIVEN** the workspace and repository contain different bytes for one
  referenced logical path
- **WHEN** the learner runs figure synchronization with direction `check`
- **THEN** the report identifies the difference and neither file changes

#### Scenario: Push workspace edits

- **GIVEN** every referenced figure required for push exists in the workspace
- **WHEN** figure synchronization runs with direction `push`
- **THEN** the repository figure area receives the workspace bytes

#### Scenario: Pull repository edits

- **GIVEN** every referenced figure required for pull exists in the repository
- **WHEN** figure synchronization runs with direction `pull`
- **THEN** the workspace receives the repository bytes

#### Scenario: Missing required source blocks the operation

- **GIVEN** at least one pool-referenced figure is absent from the selected
  direction's source side
- **WHEN** push or pull is requested
- **THEN** no figure file is written and the missing logical path is reported

### Requirement: Figure synchronization preserves runtime compatibility

During the figure-layout transition, workspace-side mirror operations SHALL
prefer `<workspace>/figures/<logical>` when present and SHALL fall back to the
existing `<workspace>/.lessonkit/figures/<logical>` copy. Pull SHALL write both
locations so the existing workbench renderer remains compatible until its own
runtime migration is delivered.

#### Scenario: Push while an existing Agent still writes the legacy area

- **GIVEN** a referenced figure exists only under `.lessonkit/figures/`
- **WHEN** figure synchronization pushes to the repository
- **THEN** that legacy file is accepted as the workspace source and copied
  without moving or renaming it

#### Scenario: Prefer an edited top-level asset

- **GIVEN** both workspace locations exist for one logical path and their bytes
  differ
- **WHEN** figure synchronization pushes to the repository
- **THEN** the top-level `figures/` copy is used

#### Scenario: Pull remains visible to the current workbench

- **WHEN** a repository figure is pulled
- **THEN** identical bytes are written to the top-level workspace figure area
  and the legacy `.lessonkit/figures/` compatibility area

### Requirement: Figure paths stay inside one course asset area

Every synchronized logical figure path SHALL be a relative POSIX path beginning
with the selected course id, containing no empty, `.` or `..` segment or
backslash, and ending in a supported image extension. Invalid or foreign-course
paths SHALL be refused before any write.

#### Scenario: Traversal path is refused

- **WHEN** a pool row references a figure path containing `..`, an absolute
  prefix, a backslash, or a foreign course prefix
- **THEN** figure synchronization reports the path invalid and writes nothing

### Requirement: Figure mirror does not manage Git transport

Figure synchronization SHALL read and write only the supplied local repository
checkout. It SHALL NOT invoke clone, fetch, pull, commit, push, or hosting APIs.

#### Scenario: Synchronize a local checkout

- **WHEN** any figure mirror direction runs
- **THEN** only ordinary local files are inspected or changed and Git transport
  remains the caller's responsibility
