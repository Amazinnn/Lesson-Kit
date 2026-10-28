## REMOVED Requirements

### Requirement: Paper update approval pauses conversation dispatch
**Reason**: Ordinary Paper edits now preserve progress and explicit learner intent authorizes them without a second approval click.
**Migration**: Route clear authorized operations through the shared adaptive mutation path, with current-state guards and truthful impact receipts. Persisted legacy approvals SHALL remain inert and cancellable; they SHALL NOT execute automatically on upgrade, reload or queue continuation. Their original conversation scope and manual queue continuation remain until cancelled or explicitly resubmitted under the new rules. Rollback approvals remain unchanged.

## ADDED Requirements

### Requirement: Explicitly authorized lifecycle actions execute without reset approval
Clear learner instructions SHALL authorize bounded archive, restore, replacement and Paper edits through supported tools without a separate ordinary Paper-reset approval. Ambiguous targets or duplicate identity SHALL require clarification, not guessed writes. Receipts SHALL identify affected questions/Papers, replacement mappings, retained history, items needing new answers and affected derived results. A stale operation SHALL be reassessed against current state within the original authorization or clarified when its scope changes. Full restart and historical correction SHALL require their own explicit instructions. Success SHALL be claimed only after confirmed writes, and reply text SHALL NOT substitute for execution evidence.

#### Scenario: Remove a specified duplicate
- **WHEN** the learner clearly names the duplicate to archive
- **THEN** the Agent executes the governed operation and reports affected Papers without requesting a redundant reset approval

#### Scenario: Duplicate target is ambiguous
- **WHEN** multiple candidates match the learner's description
- **THEN** the Agent asks which target to change and performs no guessed mutation

#### Scenario: Historical reset is not authorized
- **WHEN** the learner requests a Paper reorder
- **THEN** the Agent preserves progress and does not infer permission to restart or correct historical verdicts
