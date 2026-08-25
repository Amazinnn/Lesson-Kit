## ADDED Requirements

### Requirement: Free Agent conversation column

The right column SHALL provide free conversation on every workbench page without requiring a current problem. It SHALL show available providers, the current conversation, up to ten recent conversations, new conversation, successful messages and current turn events, an input, and a temporary stop control while running. Visible explain and diagnose shortcuts SHALL be removed while their existing APIs remain compatible.

#### Scenario: Start a free conversation

- **WHEN** the learner selects an available Agent and creates a conversation
- **THEN** the provider is locked for that conversation and the learner can send an ordinary message from the current page

#### Scenario: Restore a recent conversation

- **WHEN** the learner selects one of the workspace's ten recent conversations
- **THEN** its successful exchange mirror is rendered and later turns resume its provider-native session

#### Scenario: Stop a running turn

- **WHEN** a turn is running
- **THEN** send is disabled, a temporary stop control is visible, and cancellation reports its final state without switching provider

### Requirement: Authoritative page context for Agent turns

For each turn, the browser SHALL send object identifiers rather than page DOM, and the server SHALL rebuild authoritative workspace, course, chapter, route, page type, selected object, and relevant learning context from SQLite. Practice, knowledge-point, and graph pages SHALL respectively attach their defined object/state summaries. The latest three different browser-session object anchors SHALL also be attached. Unsubmitted answer and note drafts SHALL be excluded unless the learner explicitly enables the practice-only draft option for that turn.

#### Scenario: Ask about a knowledge point page

- **WHEN** the learner sends a turn from a knowledge-point page
- **THEN** the Agent receives current content, state, signals, schedule, neighbours, and related problems rebuilt from the workspace

#### Scenario: Keep a practice draft private

- **WHEN** an unsubmitted answer exists and the learner has not enabled draft attachment
- **THEN** the answer and note are absent from Agent context and are not persisted by the conversation bridge

#### Scenario: Attach a practice draft explicitly

- **WHEN** the learner enables draft attachment for a turn
- **THEN** only that turn receives the current answer draft in addition to the authoritative practice context

### Requirement: Learner-controlled daily conversation

Daily automatic conversation creation SHALL default off. When enabled, it SHALL use the browser's local date and create at most one conversation on the first workspace entry of that date, without interrupting a running conversation.

#### Scenario: Enter on a new local date with daily creation enabled

- **WHEN** no conversation was automatically created for that browser-local date and no turn is running
- **THEN** one new conversation is created with the learner's selected provider
