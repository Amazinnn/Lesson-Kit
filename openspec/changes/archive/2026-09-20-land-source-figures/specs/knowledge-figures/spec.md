## MODIFIED Requirements

### Requirement: Declared figure area

The figure area SHALL be the workspace's `.lessonkit/figures/{course}/{chapter}/`
directory, following the project convention that runtime files live in hidden
dot-directories. Figure files SHALL be named by their content hash,
`<sha256-hex>.<original extension>`, so identical images deduplicate naturally
and the name itself verifies provenance. The pool SHALL store only logical
paths (`{course}/{chapter}/{name}`), and each display surface resolves them
itself.

#### Scenario: A knowledge point figure is stored in the figure area

- **WHEN** the extraction pipeline lands a figure for a knowledge point
- **THEN** the file is written to `.lessonkit/figures/{course}/{chapter}/` under its content-hash name and the logical path is stored on the knowledge point

#### Scenario: The name verifies the content

- **WHEN** a figure file lands in the figure area through the gated channel
- **THEN** its name is the SHA-256 of the file bytes with the source extension, computed by the gate rather than claimed by the manifest

## ADDED Requirements

### Requirement: Gated figure patch channel

Problem figures SHALL enter the pool only through a figure-patch gate: a
manifest carries the figure source files and the full replacement problem text,
the gate verifies each source exists and hashes to its derived name, that the
text references every figure, and that no destination conflicts, and only then
does one transaction copy the files, update the problem text, and record the
logical paths on `figure_paths`. Any gate failure SHALL write nothing. An
applied patch SHALL be recorded as a batch with a snapshot carrying the
previous text and figure paths, and rollback SHALL restore them without
touching the problem's original ingest batch stamp.

#### Scenario: A patch lands figures and text together

- **WHEN** a figure-patch manifest passes the gate and is applied
- **THEN** the figure files exist under the figure area, the problem text references their logical paths, `figure_paths` lists them, and the problem's original ingest batch stamp is unchanged

#### Scenario: A gate failure writes nothing

- **WHEN** a manifest names a missing source file, an unsupported file type, a text missing a figure reference, or a conflicting destination
- **THEN** the apply fails, no file is copied, and no pool row changes

#### Scenario: Rollback restores the previous text

- **WHEN** a figure-patch batch is rolled back
- **THEN** each affected problem's text and figure paths return to their pre-patch values, and the landed figure files are left in place as content-addressed, unreferenced assets

### Requirement: Legacy source-image migration

Problems whose text still references source-extracted images by their
extraction-time relative paths SHALL be migratable in one command: the migration
locates each referenced file under the workspace, derives the content-hash name,
rewrites the references to logical paths, and applies the result through the
same gated figure-patch channel. Without the explicit apply flag the migration
SHALL report the planned changes without writing anything.

#### Scenario: Migrating embedded source images

- **WHEN** the migration runs with apply on problems referencing `images/…` files that exist under the workspace
- **THEN** every reference becomes a logical figure path, the files land under the figure area under their content-hash names, and the practice page renders them

#### Scenario: A missing source file blocks the migration

- **WHEN** a referenced image cannot be found under the workspace
- **THEN** the migration reports the problem and file and writes nothing
