## ADDED Requirements

### Requirement: Supported content writes coordinate Paper execution invalidation
All supported question edits SHALL use one Data-owned answering-content comparison and invalidation rule, including explicit patches, repository synchronization and governed Agent actions. All supported question deletions SHALL clean current Paper/checkpoint/draft references without erasing historical learning evidence. Updating a Paper SHALL NOT update question fields merely to synchronize its container. Existing batch rollback protection for dependent learning evidence SHALL remain until separately reconciled; this requirement SHALL NOT authorize arbitrary dependent-history deletion or direct SQL bypasses.

#### Scenario: The same correction arrives through different writers
- **WHEN** an equivalent semantic question correction is made by a patch, synchronized content or a governed Agent action
- **THEN** each preserves the question ID and applies the same affected-item-only reset and stale-submit boundary

#### Scenario: Rename or reset a Paper
- **WHEN** a Paper-only operation renames or resets its execution progress
- **THEN** question content, classification, ownership and learning evidence remain unchanged
