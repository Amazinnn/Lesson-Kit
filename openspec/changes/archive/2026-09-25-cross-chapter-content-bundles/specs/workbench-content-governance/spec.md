## MODIFIED Requirements

### Requirement: Atomic staged content bundle

A `content-bundle` SHALL contain one or more new knowledge points, formal
problems, micro quizzes, flash cards, and required source figures. Its manifest
SHALL be staged under the owning conversation. Every knowledge point, problem,
and flash card SHALL be assignable to exactly one chapter: an item MAY declare
its own `chapter`, otherwise the bundle-level `chapter` applies, otherwise the
workspace's active chapter; an item left without a chapter SHALL be refused with
its label and nothing SHALL be written. A single bundle MAY therefore span
several chapters, and every derived value SHALL follow its item's chapter —
allocated id prefix, figure logical path and destination directory, micro-quiz
id, and the duplicate check. The complete bundle SHALL be prevalidated and
applied under one backup and one transaction; any invalid entity, reference, or
file SHALL leave both SQLite and the figure destination unchanged. It SHALL
record one batch per chapter present, in chapter order, so each chapter's content
can be rolled back on its own. There SHALL be no fixed ceiling on items or on
chapters per bundle.

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

- **WHEN** a bundle has no chapter of its own, the workspace has no active chapter, and an item declares none
- **THEN** that item is refused with its label and no content and no figure is written

#### Scenario: A declared chapter is not an identifier

- **WHEN** an item or the bundle declares a chapter that is not a lowercase ASCII identifier
- **THEN** the bundle is refused with that reason and nothing is written

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
