## ADDED Requirements

### Requirement: Version-controlled figure assets

The authored-content repository SHALL support binary figure assets under
`figures/<course-id>/...` in addition to the JSON authored-content projection.
The pool's `knowledge_points.figure_paths` and `problems.figure_paths` SHALL
remain the authority for which logical figures belong to authored content. Image
bytes SHALL NOT be stored in SQLite or embedded in JSON entity envelopes. The
per-course `_index.json` SHALL be a derived navigation file, not a second source
of figure membership.

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
may overwrite the opposite side. The installed CLI SHALL exit with code 2 for
invalid or conflicting figure or index state, including a rejected filesystem
path.

#### Scenario: Compare differing figure bytes

- **GIVEN** the workspace and repository contain different bytes for one
  referenced logical path
- **WHEN** the learner runs figure synchronization with direction `check`
- **THEN** the report identifies the difference and neither file changes

#### Scenario: Push an eligible workspace edit

- **GIVEN** every referenced figure required for push exists in the workspace
  and its legacy hash copies, if any, agree
- **WHEN** figure synchronization runs with direction `push`
- **THEN** the repository figure area receives the workspace bytes

#### Scenario: Pull an eligible repository edit

- **GIVEN** every referenced figure required for pull exists in the repository,
  any legacy hash path has a workspace baseline, and all existing copies agree
- **WHEN** figure synchronization runs with direction `pull`
- **THEN** the workspace receives the repository bytes

#### Scenario: Preserve an existing legacy hash identity

- **GIVEN** a logical path has a filename stem of 64 lowercase hexadecimal
  characters and two or more existing workspace/repository copies have
  different bytes
- **WHEN** the learner requests `check`, `push`, or `pull`
- **THEN** the asset is reported as a conflict, every existing copy stays
  unchanged, and no other figure or index file is written by that operation

#### Scenario: Refuse a repository-only legacy hash pull

- **GIVEN** a 64-hex logical path exists in the repository but neither workspace
  copy exists
- **WHEN** the learner requests `pull`
- **THEN** the operation reports a conflict and writes no workspace file because
  no local bytes establish the existing identity

#### Scenario: Use an existing local legacy hash baseline

- **GIVEN** at least one workspace copy exists for a 64-hex logical path and all
  other existing copies contain the same bytes
- **WHEN** the learner explicitly pushes or pulls that figure
- **THEN** the matching bytes may be copied to a missing location while the
  logical path and its owners remain unchanged

Other existing logical paths that do not use this legacy hash form remain
eligible for byte edits through an explicitly selected direction. The broader
naming strategy remains unresolved; this rule does not rename paths or introduce
a new hash computation.

#### Scenario: Missing required source blocks the operation

- **GIVEN** at least one pool-referenced figure is absent from the selected
  direction's source side
- **WHEN** push or pull is requested
- **THEN** no figure file is written and the missing logical path is reported

### Requirement: Figure synchronization preserves runtime compatibility

During the figure-layout transition, workspace-side mirror operations SHALL
prefer `<workspace>/figures/<logical>` when present and SHALL fall back to the
existing `<workspace>/.lessonkit/figures/<logical>` copy after the legacy hash
identity check passes. Pull SHALL write both locations so the existing
workbench renderer remains compatible until its own runtime migration is
delivered.

#### Scenario: Push while an existing Agent still writes the legacy area

- **GIVEN** a referenced figure exists only under `.lessonkit/figures/`
- **WHEN** figure synchronization pushes to the repository
- **THEN** that legacy file is accepted as the workspace source and copied
  without moving or renaming it

#### Scenario: Prefer an edited top-level asset

- **GIVEN** both workspace locations exist for one non-hash logical path and
  their bytes differ
- **WHEN** figure synchronization pushes to the repository
- **THEN** the top-level `figures/` copy is used

Legacy 64-hex identities with differing copies SHALL follow the conflict rule
under `Figure synchronization is explicitly directional` instead of choosing a
workspace source.

#### Scenario: Pull remains visible to the current workbench

- **WHEN** a repository figure is pulled
- **THEN** identical bytes are written to the top-level workspace figure area
  and the legacy `.lessonkit/figures/` compatibility area

### Requirement: Read figure references from a managed pool

Figure synchronization SHALL read references only from an existing regular
pool database containing both the `knowledge_points` and `problems` owner tables
with their owner id columns. A missing/non-file database or a database without
either table SHALL be reported as invalid; it SHALL NOT be created or treated
as an empty reference list. For compatibility, an existing owner table without
a `figure_paths` column SHALL contribute no figure references without any schema
migration.

#### Scenario: Refuse a missing or non-file pool database

- **GIVEN** the selected workspace database path is missing or resolves to a
  non-file, or either owner table lacks its id column
- **WHEN** the learner runs figure `check`, `push`, or `pull`
- **THEN** the command reports invalid input, exits with code 2, and does not
  create a database or write a figure index

#### Scenario: Refuse an empty or unrelated database

- **GIVEN** the selected SQLite file is empty or lacks the managed owner tables
  or their id columns
- **WHEN** the learner runs figure synchronization
- **THEN** it reports invalid input and does not generate an empty owner index

#### Scenario: Read a legacy pool without figure columns

- **GIVEN** both owner tables and id columns exist but one or both tables lack
  `figure_paths`
- **WHEN** the learner runs figure synchronization
- **THEN** those absent columns contribute no references and no schema is changed

### Requirement: Figure paths stay inside one course asset area

Every synchronized logical figure path SHALL be a relative POSIX path beginning
with the selected course id, containing no empty, `.` or `..` segment or
backslash, and ending in a supported image extension. Invalid or foreign-course
paths SHALL be refused before any write. Resolved workspace asset roots and
targets SHALL remain inside the registered workspace. Resolved repository asset
roots, figure targets, and the derived index path SHALL remain inside the
supplied checkout. A root or target redirected through a symlink or junction
outside its anchor SHALL be refused before that path is read or written.

#### Scenario: Traversal path is refused

- **WHEN** a pool row references a figure path containing `..`, an absolute
  prefix, a backslash, or a foreign course prefix
- **THEN** figure synchronization reports the path invalid and writes nothing

#### Scenario: Refuse a redirected asset root

- **GIVEN** the top-level or legacy workspace figure root, or the repository
  `figures/` root, resolves outside its workspace or checkout
- **WHEN** a figure synchronization direction runs
- **THEN** the operation refuses the path before reading or writing outside the
  anchored root

#### Scenario: Preflight the owner index without figure references

- **GIVEN** no pool row references a figure and the repository course index path
  resolves outside the supplied checkout
- **WHEN** the learner requests `check` or `push`
- **THEN** the operation refuses the index path before reading or writing it

#### Scenario: Preflight the index before copying figures

- **GIVEN** the derived repository index path resolves outside the supplied
  checkout
- **WHEN** a push is planned, even if figure assets are also ready to copy
- **THEN** the operation refuses before copying any figure asset

### Requirement: Derived figure owner index

The repository SHALL store one UTF-8 JSON owner index at
`figures/<course-id>/_index.json`. It SHALL contain `schema_version` (integer
`1`), `course_id`, and `figures`; each figure entry SHALL contain its full
`logical_path` and every referencing owner as `{owner_type, owner_id}`. Push
SHALL generate the index from current pool references, including when the
reference list is empty. Check SHALL report missing, matching, different, or
invalid index content without rewriting it. Editing the index SHALL NOT change
pool references.

#### Scenario: Push writes the canonical owner index

- **GIVEN** one or more valid pool figure references
- **WHEN** the learner requests `push`
- **THEN** `_index.json` lists each logical path and all of its owners from the
  pool

#### Scenario: Push writes an empty owner index

- **GIVEN** no pool row references a figure
- **WHEN** the learner requests `push`
- **THEN** `_index.json` is still generated with an empty `figures` array

#### Scenario: Check a malformed owner index

- **GIVEN** `_index.json` is malformed or has a non-object JSON value
- **WHEN** the learner requests `check`
- **THEN** the report marks the index invalid, does not rewrite it, and the CLI
  exits with code 2

### Requirement: Figure mirror does not manage Git transport

Figure synchronization SHALL read and write only the supplied local repository
checkout. It SHALL NOT invoke clone, fetch, pull, commit, push, or hosting APIs.

#### Scenario: Synchronize a local checkout

- **WHEN** any figure mirror direction runs
- **THEN** only ordinary local files are inspected or changed and Git transport
  remains the caller's responsibility
