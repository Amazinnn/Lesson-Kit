## MODIFIED Requirements

### Requirement: The default Agent view is a session list
When the current tab has no open conversation, the Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require explicit available-provider selection, and provider ownership SHALL remain immutable. Rename/delete SHALL remain in compact history-row menus.

The chat view SHALL remain conversation-first: accessible icon return-to-list control, message stream, compact context chips and composer. Provider/session settings, daily-create controls and chat-page rename/delete SHALL NOT crowd that view. The client SHALL NOT revive provider-memory/daily-create keys or the removed explain/diagnose console. Same-workspace middle navigation SHALL NOT initialize the rail again.

#### Scenario: Chat is quiet
- **WHEN** the learner opens an existing conversation
- **THEN** the rail presents conversation, compact context and currently relevant message controls without unrelated settings or task dashboards

#### Scenario: History is the first view
- **WHEN** a workbench page opens with no conversation selected in the current tab
- **THEN** the rail shows the session list and no conversation is opened or created

#### Scenario: Return to history
- **WHEN** the learner explicitly uses the back icon
- **THEN** history returns without creating a session or learning record

#### Scenario: History row actions
- **WHEN** the learner chooses rename/delete from a history-row menu
- **THEN** the corresponding local mirror action runs and those controls remain absent from chat view

### Requirement: Agent rail keeps the open conversation across page navigation
Within the same workspace, switching the central view, its query state or browser back/forward SHALL keep the Agent rail instance and its selected conversation, draft/caret/focus, scroll position and current streaming/polling state intact. It SHALL NOT transiently return to the list, destroy/recreate the rail or rebuild conversation history merely to navigate the middle page. Current-page context chips SHALL update.

A full same-tab reload SHALL restore the selected conversation. Returning to the list SHALL require explicit learner action. A confirmed missing conversation SHALL fall back to the list without an error wall or creating a conversation. Other read errors SHALL retain the selection and show recoverable feedback. Workspace boundaries SHALL retain their existing isolation.

#### Scenario: Switch the central view
- **WHEN** a conversation is open and the learner navigates between practice, Papers, KP detail, graph or records in the same workspace
- **THEN** the existing rail DOM/controller remains mounted with draft/scroll/stream intact, no list is shown and only middle-owned resources are replaced

#### Scenario: Reload the page
- **WHEN** the learner fully reloads the workspace in the same tab
- **THEN** the selected conversation is restored without creating another session

#### Scenario: Return to the list explicitly
- **WHEN** the learner uses the return-to-list control
- **THEN** the list returns and later middle navigation/reload preserves that explicit selection state

#### Scenario: The open conversation disappears
- **WHEN** the selected conversation is confirmed missing in the workspace
- **THEN** the rail shows the list without an error wall and creates no conversation

#### Scenario: Restoring the open conversation temporarily fails
- **WHEN** a conversation read fails without confirmed deletion
- **THEN** the selection and recoverable message text are retained and the UI offers a recoverable error rather than discarding the conversation

#### Scenario: Navigate back while an answer streams
- **WHEN** the user changes the middle route and then uses browser Back during streaming
- **THEN** only the middle route changes; the same turn/poll ownership, unsent draft and deliberate scroll position survive

Activity progress surfaces, Float collapse/reopen behavior, idle cleanup, and Bottom Dock retirement are specified only in the independent `use-collapsible-agent-activity-float` change.

## ADDED Requirements

### Requirement: Existing approval controls remain truthful and scoped
Existing governed Paper-reset and rollback confirmations SHALL show their exact impact and remain bound to the intended workspace/conversation/message/revision; cancellation or stale approval SHALL perform no write. This change adds no new approval gate.

#### Scenario: Cancel an existing Paper reset approval
- **WHEN** the learner cancels a governed Paper-reset approval or switches conversations before deciding
- **THEN** no Paper write occurs and the existing approval callback cannot act on the new conversation
