## ADDED Requirements

### Requirement: Figures participate in the atomic content bundle

Required source figures SHALL be prevalidated with their new problems and
knowledge points. Supported files SHALL be copied byte for byte from any local
source path into `.lessonkit/figures/{course}/{chapter}/`; no crop, enhancement,
format conversion, or redraw is permitted. Final problem Markdown SHALL refer
to the stored logical path, and linked-problem rendering SHALL display it.

#### Scenario: Import a diagram-dependent problem

- **WHEN** a content bundle contains a valid source problem and its required original image
- **THEN** both commit under the same batch and the knowledge-point problem row displays the image

#### Scenario: Figure validation fails

- **WHEN** the source file is missing, unsupported, conflicting, or not referenced by final text
- **THEN** the whole content bundle writes neither the problem nor any figure

### Requirement: Rollback deletes newly unreferenced figures

Rolling back a content bundle SHALL remove each figure file created by that
batch when no surviving pool row references its logical path. A file still
referenced by another row SHALL remain.

#### Scenario: Unique bundle image is rolled back

- **WHEN** the owning batch is rolled back and no other row references its image
- **THEN** the database reference and physical file are both removed

#### Scenario: Shared image remains referenced

- **WHEN** another surviving problem still references the same logical image
- **THEN** rollback removes only the rolled-back row's reference and retains the file

