## MODIFIED Requirements

### Requirement: Declared figure area

The figure area SHALL be the workspace's `.lessonkit/figures/{course}/{chapter}/`
directory, following the project convention that runtime files live in hidden
dot-directories. Figure files landed through the gated figure channel SHALL be
named by their content hash, `<sha256-hex>.<original extension>`, so identical
images deduplicate naturally and the gate-derived name verifies those bytes.
This naming rule does not decide the repository-wide policy for every logical
reference. The pool SHALL store only logical paths
(`{course}/{chapter}/{name}`), and each display surface resolves them itself.

An explicit JSON mirror revision MAY replace `figure_paths` for an already-
tracked knowledge point or problem when each logical path passes the existing
course-relative figure path validation. This projection updates only the
reference array: it SHALL NOT create, copy, rename, or inspect figure bytes,
compute a byte hash, or assert that referenced bytes exist. Missing physical
files SHALL continue to follow the existing missing-figure and binary-check
behavior.

#### Scenario: A knowledge point figure is stored in the figure area

- **WHEN** the extraction pipeline lands a figure for a knowledge point
- **THEN** the file is written to `.lessonkit/figures/{course}/{chapter}/` under its content-hash name and the logical path is stored on the knowledge point

#### Scenario: The name verifies the content

- **WHEN** a figure file lands in the figure area through the gated channel
- **THEN** its name is the SHA-256 of the file bytes with the source extension, computed by the gate rather than claimed by the manifest

#### Scenario: JSON mirror updates logical references without asserting figure bytes

- **GIVEN** a knowledge point or problem is already tracked by the JSON mirror
- **WHEN** an explicit next revision changes its `figure_paths` to course-relative references accepted by the existing path validation
- **THEN** sync stores the reference array without checking that the referenced bytes exist or changing any figure file or binary index
- **AND** any missing-file behavior remains governed by the existing missing-figure and binary-check policy

#### Scenario: An invalid mirrored reference leaves its owner unchanged

- **GIVEN** a course-level JSON sync contains one tracked owner with an invalid figure reference and another tracked owner with a valid update
- **WHEN** the mirror plans or synchronizes both entities
- **THEN** the invalid owner is rejected before its pool row, JSON file, mirror state, or mirror log is written, while the valid owner follows the existing per-entity synchronization behavior
- **AND** neither entity operation creates or changes figure bytes or a binary index

### Requirement: Gated figure patch channel

Creating or attaching new problem figure assets SHALL occur only through a
figure-patch gate. Its manifest carries the figure source files and the full
replacement problem text; the gate verifies each source exists and hashes to
its derived name, that the text references every figure, and that no
destination conflicts, and only then does one transaction copy the files,
update the problem text, and record the logical paths on `figure_paths`. Any
gate failure SHALL write nothing. An applied patch SHALL be recorded as a
batch with a snapshot carrying the previous text and figure paths, and rollback
SHALL restore them without touching the problem's original ingest batch stamp.

An explicit JSON mirror revision is a separate reference-field projection for
an already-tracked problem. It MAY update `figure_paths` after existing logical
path validation, but SHALL NOT create, copy, rename, or transport figure bytes,
change problem text as part of image generation, compute or attest a byte hash,
or claim that the referenced files exist or are intact. New problem image
generation and asset attachment remain subject to this gated manifest, review,
source-byte, and hash-verification channel.

#### Scenario: A patch lands figures and text together

- **WHEN** a figure-patch manifest passes the gate and is applied
- **THEN** the figure files exist under the figure area, the problem text references their logical paths, `figure_paths` lists them, and the problem's original ingest batch stamp is unchanged

#### Scenario: A gate failure writes nothing

- **WHEN** a manifest names a missing source file, an unsupported file type, a text missing a figure reference, or a conflicting destination
- **THEN** the apply fails, no file is copied, and no pool row changes

#### Scenario: Rollback restores the previous text

- **WHEN** a figure-patch batch is rolled back
- **THEN** each affected problem's text and figure paths return to their pre-patch values, and the landed figure files are left in place as content-addressed, unreferenced assets

#### Scenario: Reference-only mirror updates do not bypass the figure gate

- **GIVEN** a problem is already tracked and has a valid JSON mirror projection
- **WHEN** the projection changes only its `figure_paths` reference array
- **THEN** the mirror updates that field without changing problem text or figure bytes, and any new image generation or asset attachment still requires the gated figure-patch channel
