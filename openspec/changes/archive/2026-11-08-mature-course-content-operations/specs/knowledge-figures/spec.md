## REMOVED Requirements

### Requirement: Rollback deletes newly unreferenced figures

**Reason**: Q098/S008 retires explicit undo of successfully applied content batches.
**Migration**: Use governed direct content repair. Existing referenced images and historical data remain governed by their normal content lifecycle.

## MODIFIED Requirements

### Requirement: Gated figure patch channel

Creating or attaching new problem figure assets SHALL occur only through a
figure-patch gate. Its manifest carries the figure source files and the full
replacement problem text; the gate verifies each source exists, has a declared readable logical name and matches its staged source bytes, that the text references every figure, and that no
destination conflicts, and only then does one transaction copy the files,
update the problem text, and record the logical paths on `figure_paths`. Any
gate failure SHALL write nothing. An applied patch SHALL be recorded as a
batch with a snapshot carrying the previous text and figure paths, and the problem's original ingest batch stamp SHALL remain unchanged. Explicit successful-batch undo SHALL be retired.

An explicit JSON mirror revision is a separate reference-field projection for
an already-tracked problem. It MAY update `figure_paths` after existing logical
path validation, but SHALL NOT create, copy, rename, or transport figure bytes,
change problem text as part of image generation, compute or attest a byte hash,
or claim that the referenced files exist or are intact. New problem image
generation and asset attachment remain subject to this gated manifest, review,
source-byte verification channel.

Existing hash-shaped figure filenames SHALL remain valid opaque legacy paths without requiring new hash computation. New managed names SHALL use readable sequential identity and logical revisions.

#### Scenario: A patch lands figures and text together

- **WHEN** a figure-patch manifest passes the gate and is applied
- **THEN** the figure files exist under the figure area, the problem text references their logical paths, `figure_paths` lists them, and the problem's original ingest batch stamp is unchanged

#### Scenario: A gate failure writes nothing

- **WHEN** a manifest names a missing source file, an unsupported file type, a text missing a figure reference, or a conflicting destination
- **THEN** the apply fails, no file is copied, and no pool row changes

#### Scenario: Rollback restores the previous text

- **WHEN** a figure-patch batch is rolled back
- **THEN** the retired operation performs no write and ordinary direct text and figure repair remains available

#### Scenario: Reference-only mirror updates do not bypass the figure gate

- **GIVEN** a problem is already tracked and has a valid JSON mirror projection
- **WHEN** the projection changes only its `figure_paths` reference array
- **THEN** the mirror updates that field without changing problem text or figure bytes, and any new image generation or asset attachment still requires the gated figure-patch channel
