## MODIFIED Requirements

### Requirement: Local deletion is bounded
Deleting an idle session SHALL remove only its Lesson Kit mirror directory. A running session SHALL return a conflict and remain intact. The identifier SHALL be validated as a plain generated conversation name before any filesystem call, so a request that carries a path separator or `..` is refused with an explicit error and removes nothing.

#### Scenario: Returning to history
- **WHEN** a student clicks back from a conversation
- **THEN** the list view returns without creating or modifying a learning record

#### Scenario: A traversal identifier is refused
- **WHEN** a delete or rename request carries a conversation identifier that is not a plain name
- **THEN** the request fails with an explicit error and no directory inside or outside the workspace is removed

#### Scenario: Another workspace's conversation is unreachable
- **WHEN** a delete request names a conversation that belongs to a different workspace
- **THEN** the request fails as unknown and the other workspace's jobs directory is untouched
