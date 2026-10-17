## ADDED Requirements

### Requirement: Saved Paper updates preserve container identity
An update explicitly targeting an existing Paper SHALL retain its Paper ID. Effective title/description-only or no-op changes SHALL retain unfinished execution progress. A manual change to item membership or order SHALL first report its exact progress impact and require confirmation, then reset only that Paper's unfinished progress/drafts without modifying questions, historical attempts, ratings or other Papers. Cancellation SHALL leave both content and progress unchanged. Saving SHALL NOT automatically start practice.

#### Scenario: Update the original Paper instead of creating another
- **WHEN** the caller confirms a membership/order update of a partially practiced saved Paper
- **THEN** the same Paper ID contains the new ordered items and its unfinished progress is reset, while learning evidence and other Papers remain unchanged

#### Scenario: Rename without resetting practice
- **WHEN** only a saved Paper's title or description changes
- **THEN** its unfinished state, drafts and item order remain unchanged

#### Scenario: Cancel a structure change
- **WHEN** the user rejects the displayed progress-reset impact
- **THEN** neither the Paper nor any execution or learning record changes

### Requirement: Saved container management does not depend on live item availability
The system SHALL keep saved Paper metadata visible, inspectable, repairable and deletable even when an item is missing. It SHALL report missing item identities explicitly and SHALL NOT silently omit the container from its list. Starting an invalid or empty Paper SHALL fail clearly without starting an execution or writing learning state. Deleting a Paper SHALL remove only its container and unfinished progress/drafts, preserving questions, learning evidence and historical runs with the deleted source identity/label.

#### Scenario: Repair an orphaned Paper
- **WHEN** an existing Paper references missing questions and an author explicitly supplies a valid replacement item list
- **THEN** the original container can be repaired under the confirmed update rules instead of requiring delete/re-import

#### Scenario: Delete a container whose question is missing
- **WHEN** the learner confirms deleting a saved Paper containing an unavailable question
- **THEN** the container and its unfinished state are removed without deleting any surviving question, attempt, rating or historical run

#### Scenario: Last question was removed
- **WHEN** deletion of a question leaves a saved Paper with no items
- **THEN** the empty container remains visible and manageable, and starting it is refused without learning writes

### Requirement: Corrected imports identify existing update targets explicitly
The authoring workflow SHALL distinguish creation from correction of existing Paper/question IDs. A correction SHALL use explicit existing identities and SHALL NOT infer overwrite identity from a matching title, similar question text or an answering-type prefix. Correcting a question to an objective form SHALL NOT allocate a replacement ID merely because its content type changes.

#### Scenario: Correct an existing open-form import
- **WHEN** an author explicitly targets an existing question to correct its choices or answering type
- **THEN** the existing question ID remains and existing Paper membership/order is unchanged
