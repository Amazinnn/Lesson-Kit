# Agent session list

## ADDED Requirements

### Requirement: The default Agent view is a session list
The right column SHALL initially show all local sessions with title, provider, updated time, and status. It SHALL not automatically open a session or create one.

#### Scenario: History is the first view
- **WHEN** a workbench page loads
- **THEN** the Agent column shows the session list and no session is opened or created

### Requirement: Provider is selected once
New-session flow SHALL require an explicit available provider choice before creation. A created session SHALL display its provider as read-only.

#### Scenario: Provider is locked after creation
- **WHEN** a student creates a session with Codex
- **THEN** the conversation view shows Codex without a provider switch control

### Requirement: Session title is explicit
The mirror SHALL store `title` and `title_source`. A successful provider result MAY supply a title only when the session is unset; an explicit user rename SHALL take precedence.

#### Scenario: User title wins
- **WHEN** a student renames a session after an Agent title was received
- **THEN** later turns do not replace the user title

### Requirement: Local deletion is bounded
Deleting an idle session SHALL remove only its Lesson Kit mirror directory. A running session SHALL return a conflict and remain intact.

#### Scenario: Returning to history
- **WHEN** a student clicks back from a conversation
- **THEN** the list view returns without creating or modifying a learning record
