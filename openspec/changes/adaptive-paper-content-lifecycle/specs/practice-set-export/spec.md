## MODIFIED Requirements

### Requirement: Saved Paper updates preserve container identity
An explicit update SHALL retain the Paper ID. Membership/order edits SHALL reconcile unfinished execution state by surviving question identity, preserving answers, drafts, submission locks, reveal facts and Attempt links of unchanged items. New or replacement questions SHALL begin pending. Removed items SHALL retain their historical answer/draft associations. Title/description-only and no-op edits SHALL preserve progress. Clear learner instructions SHALL authorize the operation without a separate reset-approval click; stale expected structure or execution state SHALL cause no write. Saving SHALL NOT start practice. Full restart SHALL require a separate explicit instruction.

#### Scenario: Update the original Paper instead of creating another
- **WHEN** an authorized caller removes one duplicate from a partially practiced Paper
- **THEN** the same Paper retains surviving item progress without resetting the execution or modifying unrelated Papers or learning evidence

#### Scenario: Reorder and add items
- **WHEN** an authorized caller reorders surviving questions and adds a question
- **THEN** surviving states follow their identities, the added question is pending, and the cursor remains on its surviving question or the nearest following survivor, otherwise the preceding survivor

#### Scenario: Rename without resetting practice
- **WHEN** only title or description changes
- **THEN** unfinished states, drafts and item order remain unchanged

#### Scenario: Reject a stale operation
- **WHEN** expected Paper or execution state no longer matches
- **THEN** no content or progress changes and the caller receives the current impact for reassessment

#### Scenario: Cancel a structure change
- **WHEN** the caller cancels an inspected change before execution
- **THEN** neither Paper content nor execution state changes; an already committed authorized operation is not retroactively cancelled

### Requirement: Saved container management does not depend on live item availability
Saved Paper metadata SHALL remain inspectable and repairable even with missing items. Missing identities SHALL be reported explicitly. Starting an invalid or empty Paper SHALL fail without learning writes. Deletion SHALL archive the Paper, retaining its definition, identity, unfinished progress, drafts and history while hiding it from default current listings and execution entry points. Questions SHALL remain unchanged. Explicit restoration SHALL reconcile retained state against latest available content without restoring archived questions. Empty Papers SHALL remain manageable and SHALL NOT fabricate completion.

#### Scenario: Repair an orphaned Paper
- **WHEN** an author supplies a valid replacement list for a Paper with missing questions
- **THEN** the original container is repaired through adaptive reconciliation

#### Scenario: Delete a container whose question is missing
- **WHEN** a Paper with unavailable items is archived and later explicitly restored
- **THEN** its identity and history survive, remaining available items use current content, and unavailable items are reported without fabricated replacements

#### Scenario: Last question was removed
- **WHEN** all current questions are removed
- **THEN** the Paper remains empty and unfinished, retained historical drafts remain readable, and subsequent item additions permit practice

### Requirement: Corrected imports identify existing update targets explicitly
Corrections SHALL explicitly target an existing question identity, never infer overwrite from title, similar text or prefix. An answering-semantic correction SHALL create a replacement identity and report old/new IDs; all current Paper references SHALL substitute the replacement at the same positions. Metadata-only corrections SHALL keep the identity. Current Paper edits SHALL NOT modify question fields as a side effect.

#### Scenario: Correct an existing open-form import
- **WHEN** an explicit correction changes choices or answering type
- **THEN** a new question replaces the archived target in current Papers without changing order or unrelated progress
