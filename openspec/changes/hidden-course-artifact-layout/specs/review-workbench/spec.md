## ADDED Requirements

### Requirement: Hidden workspace artifact layout

New workspaces SHALL place the Knowledge Pool in `.lessonkit/pool/<course>.db` and Lesson Kit internal build artifacts under `.lessonkit/intermediate/`. Existing `.lessonkit/` figures, conversations, plans and saved Papers SHALL keep their paths. Internal/default generated files SHALL remain under `.lessonkit/`; a user-specified export destination SHALL be honored. Maintained Agent instructions SHALL distinguish internal work from an explicitly requested export. External tools' own folders and course source materials SHALL NOT be relocated by this policy.

#### Scenario: Initialize a new course without root internal directories

- **WHEN** a new course workspace is initialized
- **THEN** its registered database is `.lessonkit/pool/<course>.db`, normal internal output stays hidden, and root `pool/` and `intermediate/` are not created

#### Scenario: Continue using an unmigrated course

- **WHEN** an existing registered course still uses root `pool/`
- **THEN** opening, initializing again, reading and writing it retain that layout until explicit migration, without creating or adopting a replacement pool

#### Scenario: Resolve conflicting pool layouts explicitly

- **WHEN** discovery finds conflicting candidate pools in both layouts without an unambiguous explicit selection
- **THEN** it refuses instead of silently adopting a different pool

#### Scenario: Separate internal work from export

- **WHEN** Lesson Kit or its Agent produces an internal artifact without a user-specified external export destination
- **THEN** it writes under `.lessonkit/` without creating a course-root output directory
- **AND** an explicitly requested export to another destination remains supported

#### Scenario: Validate new hidden work while the pool remains legacy

- **WHEN** an unmigrated course creates hidden gate-specific artifacts
- **THEN** the installed Workbench guard validates that hidden directory without requiring a local copy of `lessonkit.py`
- **AND** incomplete hidden work fails instead of passing against stale root artifacts, while root-only legacy work remains supported

#### Scenario: Resolve legacy images across old and new internal work

- **WHEN** legacy image-reference planning finds a referenced image in the new hidden intermediate area or the old root area
- **THEN** it can read that source without relocating the pool
- **AND** conflicting same-name images across both areas are reported before application instead of silently choosing different content

#### Scenario: Keep default results hidden for an unmigrated course

- **WHEN** an unmigrated course runs an ingest task without an explicit result destination
- **THEN** the result is written under `.lessonkit/`, even when the input task is external
- **AND** the input task remains intact and an explicit external result destination is still honored

### Requirement: Explicit workspace layout migration

The human CLI SHALL expose `lesson-kit workspace <name> migrate-layout`, with preview as the default and mutation requiring `--apply`. Migration SHALL move only the workspace-root `pool/` and `intermediate/` into `.lessonkit/`, preserve all contained history/backups, update database registration and keep affected internal path references resolvable. It SHALL NOT alter content/schema/learning semantics, prune history, move existing exports/course materials/external tool directories, or traverse and merge nested workspace copies. It SHALL preflight conflicts/containment, refuse unsafe active-work mutation, and leave usable registration and source files on failure. A completed migration SHALL be safe to repeat without creating copies.

#### Scenario: Preview without mutation

- **WHEN** the migration command runs without `--apply`
- **THEN** it reports the planned source/destination moves and registration change without changing files or registry

#### Scenario: Migrate a course with historical files

- **WHEN** explicit migration applies to an idle legacy workspace with no destination conflicts
- **THEN** all pool backups, batch records and intermediate files are retained in the hidden destinations, the registered pool opens there, and affected path references continue to resolve
- **AND** saved Papers, figures and course learning data remain intact

#### Scenario: Refuse a conflicting destination before moving

- **WHEN** a destination already contains conflicting files or source paths escape the workspace
- **THEN** migration refuses without overwriting, merging or partially changing registration

#### Scenario: Preserve unrelated directories

- **WHEN** a course contains source materials, existing readable exports and a nested historical workspace copy
- **THEN** migrating the two explicitly owned root directories leaves those unrelated paths untouched

#### Scenario: Repeat a completed migration

- **WHEN** the migration command is applied again to an already migrated workspace
- **THEN** it reports no remaining moves and preserves the same registered database and all files
