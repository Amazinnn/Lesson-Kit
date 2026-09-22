## ADDED Requirements

### Requirement: Requested problem type and source form are preserved

Micro Quiz SHALL remain a supported problem type with yes/no, single-choice,
and multiple-choice subtypes, and the existing four practice entries SHALL
remain available. Importing textbook exercises SHALL preserve each source
problem's wording, numerical conditions, answer form, and problem type. A
source exercise SHALL use `origin_kind=source_problem`; it SHALL become a micro
quiz only when the source is already that type or the learner explicitly asks
for a micro adaptation. Generated simple choice/judgement questions remain
allowed with `origin_kind=generated_grounded`.

#### Scenario: Import a textbook proof

- **WHEN** a learner asks to import a textbook proof exercise without requesting adaptation
- **THEN** a formal source problem is created and no choice options are invented

#### Scenario: Explicit micro adaptation

- **WHEN** the learner asks to convert source material into a single-choice micro quiz
- **THEN** an adapted micro problem may be created with a valid structured subtype

#### Scenario: Existing micro flow remains compatible

- **WHEN** a valid micro problem is pulled through the existing small-quiz or yes/no entry
- **THEN** its current structured answering and feedback behavior remains available

### Requirement: Atomic staged content bundle

A `content-bundle` SHALL contain one or more new knowledge points, formal
problems, micro quizzes, flash cards, and required source figures. Its manifest
SHALL be staged under the owning conversation. The complete bundle SHALL be
prevalidated and applied under one readable batch id with one recoverable
backup; any invalid entity/reference/file SHALL leave both SQLite and the
figure destination unchanged. There SHALL be no fixed six-item ceiling.

#### Scenario: Missing knowledge point is included

- **WHEN** a source problem needs a new knowledge point included in the same bundle
- **THEN** both validate and commit together, or neither is written

#### Scenario: Required image is missing

- **WHEN** a problem depends on an unavailable or invalid source image
- **THEN** the complete bundle fails and the incomplete problem is not inserted

#### Scenario: Thirty valid exercises

- **WHEN** one bundle contains thirty valid exercises and their dependencies
- **THEN** all commit under one batch id

### Requirement: Source and solution provenance

Every new Agent-managed problem SHALL store non-empty source evidence visible
to the learner. OCR errors MAY be corrected by checking the original page, but
the content SHALL NOT otherwise change the source wording, values, options, or
answer form. A source-provided short answer SHALL be stored separately from a
detailed solution. A source solution SHALL be identified as source material;
an on-demand AI explanation SHALL be identified as generated and MAY enter
without an independent semantic audit. Legacy rows MAY leave these fields null.

#### Scenario: Textbook supplies only a short answer

- **WHEN** an exercise has a source answer but no detailed solution
- **THEN** the source answer is preserved and no AI explanation is generated until requested

#### Scenario: Learner requests an explanation

- **WHEN** an AI explanation is generated on request
- **THEN** it is stored and displayed as `AI 生成解析` without overwriting the source answer

### Requirement: Completeness remains advisory

The system SHALL NOT add a deterministic source-coverage gate in this change.
An Agent MAY describe an import as complete in prose, but product/developer
documentation SHALL state that this claim is advisory and may omit source
items.

#### Scenario: Agent claims all items were imported

- **WHEN** the Agent reports completion
- **THEN** no hidden mechanical guarantee of source coverage is implied

