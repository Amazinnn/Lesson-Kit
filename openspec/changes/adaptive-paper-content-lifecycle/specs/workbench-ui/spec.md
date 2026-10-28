## REMOVED Requirements

### Requirement: Existing approval controls remain truthful and scoped
**Reason**: Its mandatory ordinary Paper-reset approval and dispatch pause are retired; unrelated rollback protection remains required by the replacement below.
**Migration**: Replace the ordinary reset approval with explicitly authorized adaptive execution. Preserve existing rollback behavior and treat old persisted Paper approvals as inert cancellable decisions, never as authority to autoexecute or resume queues.

## ADDED Requirements

### Requirement: Lifecycle actions retain scoped rollback and legacy-decision safety
Rollback confirmations SHALL retain their existing exact impact, workspace/conversation/message/revision scoping, composer-replacement interaction, cancellation and stale-decision protection. Ordinary explicitly authorized adaptive Paper edits SHALL NOT show or wait for a Paper-reset approval or pause dispatch for that obsolete gate. No generic approval gate SHALL be added to ordinary tools. Legacy persisted Paper-reset approvals SHALL remain inert and cancellable; upgrade/reload SHALL NOT autoapprove them, perform writes or automatically resume paused dispatch. Cancelled legacy decisions SHALL retain queued messages and require manual continuation. Conversation switching SHALL make old callbacks inert.

#### Scenario: Authorized adaptive edit
- **WHEN** a clear learner instruction changes a Paper list
- **THEN** the UI reports confirmed impact without a redundant reset approval or fabricated success

#### Scenario: Recover a legacy approval
- **WHEN** a persisted old Paper-reset decision is loaded
- **THEN** it is labelled obsolete, can be cancelled or explicitly resubmitted, and neither its update nor paused queue autoexecutes

#### Scenario: Rollback remains scoped
- **WHEN** a rollback decision is cancelled, stale or belongs to another conversation
- **THEN** no rollback write occurs and the existing rollback controls retain their intended scope

### Requirement: Adaptive lifecycle status is visible and truthful
Default current listings SHALL exclude archived questions/Papers and provide bounded explicit archive inspection/restoration through supported authoring operations. Restoring a Paper SHALL show current content with reconciled progress. Empty unfinished Papers SHALL show no available questions without completion or reward. Current views SHALL NOT offer old/new version selection; history SHALL expose retained old content/answers and clearly labelled unsubmitted drafts. Stale derived values SHALL be refreshed before display; failures SHALL show an actionable unavailable/update-failed state rather than an old value labelled current.

#### Scenario: Restore an archived Paper after content changed
- **WHEN** an archived Paper is explicitly restored after a referenced question was replaced or archived
- **THEN** latest available membership and preserved surviving progress appear without resurrecting archived questions

#### Scenario: Empty Paper and refresh failure
- **WHEN** the last question is removed or a needed derived-result refresh fails
- **THEN** the UI displays the corresponding empty or unavailable state without invented completion or current statistics
