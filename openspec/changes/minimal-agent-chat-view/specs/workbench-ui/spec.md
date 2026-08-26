# Minimal Agent chat view

## MODIFIED Requirements

### Requirement: Agent conversation uses list, picker, and minimal chat states
The Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require one explicit provider selection; the provider SHALL be immutable after creation. Rename and delete SHALL be available from compact history-row menus only.

The chat state SHALL contain only an icon-only return-to-list control with an accessible label, the message stream, the input area, and a stop control while a turn is running. It SHALL NOT show provider settings, session settings, identity labels, current-page context text, daily-create controls, or chat-page rename/delete controls.

The client SHALL NOT read or write provider-memory or daily-create browser keys, auto-open the first session, auto-create a daily session, or initialize the removed explain/diagnose task console. Server-side context construction and existing compatibility APIs remain unchanged.

#### Scenario: Chat is quiet

- **WHEN** a learner opens an existing conversation
- **THEN** the chat view shows only the accessible icon back control, messages, input, and any running stop control

#### Scenario: Return to history

- **WHEN** the learner activates the back icon
- **THEN** the history list returns without creating a session or learning record

#### Scenario: History row actions

- **WHEN** the learner chooses rename or delete from a history-row menu
- **THEN** the corresponding local mirror action runs; those controls are absent from chat view
