# Minimal Agent chat view

## MODIFIED Requirements

### Requirement: The default Agent view is a session list
The Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require one explicit provider selection; the provider SHALL be immutable after creation. Rename and delete SHALL be available from compact history-row menus only.

The chat state SHALL contain only an icon-only return-to-list control with an accessible label, the message stream, the input area, and a stop control while a turn is running. It SHALL NOT show provider settings, session settings, identity labels, current-page context text, daily-create controls, or chat-page rename/delete controls.

The client SHALL NOT read or write provider-memory or daily-create browser keys, auto-open the first session, auto-create a daily session, or initialize the removed explain/diagnose task console. Server-side context construction and existing compatibility APIs remain unchanged.

#### Scenario: Chat is quiet

- **WHEN** a learner opens an existing conversation
- **THEN** the chat view shows only the accessible icon back control, messages, input, and any running stop control

#### Scenario: History is the first view

- **WHEN** a workbench page loads
- **THEN** the Agent column shows the session list and no session is opened or created

#### Scenario: Return to history

- **WHEN** the learner activates the back icon
- **THEN** the history list returns without creating a session or learning record

#### Scenario: History row actions

- **WHEN** the learner chooses rename or delete from a history-row menu
- **THEN** the corresponding local mirror action runs; those controls are absent from chat view

## REMOVED Requirements

### Requirement: Learner-controlled daily conversation

Daily automatic conversation creation is removed; sessions are created only through the explicit new-session action.
