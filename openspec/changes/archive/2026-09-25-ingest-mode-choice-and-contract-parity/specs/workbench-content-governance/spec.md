## MODIFIED Requirements

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
