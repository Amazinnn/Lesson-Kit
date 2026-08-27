## ADDED Requirements

### Requirement: Fixed outer sidebar boundaries

On desktop, resizing either sidebar SHALL change only that sidebar and the flexible middle column. The left outer edge SHALL remain at the viewport left, the right outer edge SHALL remain at the viewport right, and the middle column SHALL retain at least 420px.

#### Scenario: Expand either sidebar

- **WHEN** the learner drags a sidebar edge
- **THEN** only the middle column yields space, the opposite sidebar remains visible, and the layout does not overflow

### Requirement: Chat view owns the right-column height

In chat state, the complete session-controls region SHALL be removed from layout. The compact chat header, scrollable messages, and input row SHALL fill the right column.

#### Scenario: Open a conversation

- **WHEN** the learner opens or creates a conversation
- **THEN** the session controls reserve no space above the chat
