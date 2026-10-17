## ADDED Requirements

### Requirement: Supported content writes coordinate Paper execution invalidation
All supported question edits SHALL use one Data-owned answering-content comparison and invalidation rule, including explicit patches, repository synchronization and governed Agent actions. All supported question deletions SHALL clean current Paper/checkpoint/draft references without erasing historical learning evidence. Updating a Paper SHALL NOT update question fields merely to synchronize its container. Existing batch rollback protection for dependent learning evidence SHALL remain until separately reconciled; this requirement SHALL NOT authorize arbitrary dependent-history deletion or direct SQL bypasses.

#### Scenario: The same correction arrives through different writers
- **WHEN** an equivalent semantic question correction is made by a patch, synchronized content or a governed Agent action
- **THEN** each preserves the question ID and applies the same affected-item-only reset and stale-submit boundary

#### Scenario: Rename or reset a Paper
- **WHEN** a Paper-only operation renames or resets its execution progress
- **THEN** question content, classification, ownership and learning evidence remain unchanged

## RENAMED Requirements

- FROM: `### Requirement: Transactional physical deletion`
- TO: `### Requirement: Transactional content deletion with historical preservation`

## MODIFIED Requirements

### Requirement: Transactional content deletion with historical preservation
Content deletion SHALL be atomic. Deleting a problem SHALL remove it from active pool access,
current Paper memberships and unfinished item/draft references while retaining its historical
identity and every genuine attempt, feedback, signal, progress and schedule row. A historical
question row SHALL NOT be selected for practice or edited as current content. Deleting a knowledge
point SHALL remove its relations and membership from shared problems; newly ownerless problems
SHALL follow the same history-preserving deletion rule. Deleting a relation SHALL remove only
that relation. Recoverable Paper file intents SHALL coordinate SQLite and managed JSON effects.
Existing batch rollback refusals for dependent learning evidence SHALL remain in force.

#### Scenario: Delete a problem with learning records
- **WHEN** a formal problem is explicitly deleted
- **THEN** it is unavailable in current pool access, its current Paper/item references are cleaned, and every genuine learning record remains linked to its historical identity

#### Scenario: Delete a knowledge point with shared and ownerless problems
- **WHEN** a knowledge point owns both a shared problem and a sole-owned problem
- **THEN** the shared problem remains without that membership, the sole-owned problem becomes historical with learning rows retained, and all attached relations are removed atomically

#### Scenario: A deletion step fails
- **WHEN** any statement in a content deletion transaction fails
- **THEN** the entire deletion is rolled back and the original content remains

### Requirement: Source and solution provenance
Every new Agent-managed problem SHALL store non-empty source evidence visible to the learner.
OCR errors MAY be corrected by checking the original page, but the content SHALL NOT otherwise
change the source wording, values, options, or answer form. A source-provided short answer SHALL
remain separate from a detailed solution. Solution provenance SHALL remain stored as source or
generated; legacy null values remain valid. An on-demand generated explanation MAY enter without
an independent semantic audit. Normal reveal SHALL retain useful content without adding a
standalone AI explanation panel or repeating identical explanation text.

#### Scenario: Textbook supplies only a short answer
- **WHEN** an exercise has a source answer but no detailed solution
- **THEN** the source answer is preserved and no AI explanation is generated until requested

#### Scenario: Learner requests an explanation
- **WHEN** an AI explanation is generated on request
- **THEN** its content and generated provenance are stored without overwriting the source answer; useful text appears in normal analysis, and identical already-visible text is not duplicated
