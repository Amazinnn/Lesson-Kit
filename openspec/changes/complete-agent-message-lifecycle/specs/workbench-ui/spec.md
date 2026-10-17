## MODIFIED Requirements

### Requirement: The default Agent view is a session list
When the current tab has no open conversation, the Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require explicit available-provider selection, and provider ownership SHALL remain immutable. Rename/delete SHALL remain in compact history-row menus.

The chat view SHALL remain conversation-first: accessible icon return-to-list control, message stream, compact context chips, composer, relevant pending-message controls and stop/interrupt controls. Provider/session settings, daily-create controls and chat-page rename/delete SHALL NOT crowd that view. The client SHALL NOT revive provider-memory/daily-create keys or the removed explain/diagnose console. Same-workspace middle navigation SHALL NOT initialize the rail again.

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
Within the same workspace, switching the central view, its query state or browser back/forward SHALL keep the Agent rail instance and its selected conversation, draft/caret/focus, scroll position, current streaming/polling state and pending queue intact. It SHALL NOT transiently return to the list, destroy/recreate the rail or rebuild conversation history merely to navigate the middle page. Current-page context chips SHALL update; submitted/queued/running message context SHALL remain the snapshot captured at submission.

A full same-tab reload SHALL restore the selected conversation and supported durable message/queue state. Returning to the list SHALL require explicit learner action. A confirmed missing conversation SHALL fall back to the list without an error wall or creating a conversation. Other read errors SHALL retain the selection and show recoverable feedback. Workspace boundaries SHALL retain their existing isolation.

#### Scenario: Switch the central view
- **WHEN** a conversation is open and the learner navigates between practice, Papers, KP detail, graph or records in the same workspace
- **THEN** the existing rail DOM/controller remains mounted with draft/scroll/stream/queue intact, no list is shown and only middle-owned resources are replaced

#### Scenario: Reload the page
- **WHEN** the learner fully reloads the workspace in the same tab
- **THEN** the selected conversation and supported durable outgoing/pending-message state are restored without creating another session

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

### Requirement: Agent runtime work uses transient auxiliary surfaces
Short and sustained provider activity SHALL use only the top-right replaceable Activity Float for progress and current milestones. A Bottom Dock SHALL NOT open or reserve middle-page height during work. The Float SHALL be bounded/collapsible and SHALL NOT become a history dashboard or raw event wall. Existing conversation activity/history SHALL remain authoritative. Confirmed failures SHALL show a semantic summary with folded diagnostics. Failed progress reads SHALL remain unavailable progress, not proof of provider failure.

#### Scenario: A short activity is visible
- **WHEN** a provider reports short activity
- **THEN** the Float shows its readable label/state and newer activity replaces its current summary

#### Scenario: Work continues across milestones
- **WHEN** a provider reports sustained multi-step work
- **THEN** the same top-right Float summarizes current milestones/status while the middle page keeps its height and no Bottom Dock opens

#### Scenario: Detailed output is available
- **WHEN** provider output accompanies activity
- **THEN** the Float retains a bounded semantic summary and detailed output stays behind the closed conversation disclosure

#### Scenario: A provider confirms a failure
- **WHEN** the current turn is authoritatively failed
- **THEN** a concise failure summary and known impact are available, with long/raw diagnostics folded

#### Scenario: Progress cannot be read
- **WHEN** polling fails without authoritative terminal status
- **THEN** the UI preserves current turn ownership, reports unavailable progress and does not dispatch a second task as if the first had failed

### Requirement: Explicit collapse applies to the current Agent turn
A small accessible control SHALL expand/collapse the Activity Float with a truthful label and `aria-expanded`. Collapsing SHALL leave a compact reopening control while runtime progress is available. Later same-turn activity SHALL NOT force reopening; explicit expansion MAY reopen it. A new turn SHALL reset suppression; switching conversations SHALL clear the old transient state. Idle SHALL NOT leave a placeholder panel. Existing explicit Artifact preview remains separate from task-progress display.

#### Scenario: Collapse while work is running
- **WHEN** the learner collapses the Float and another activity arrives in that turn
- **THEN** activity remains in history, the Float stays closed and the small reopen control remains available

#### Scenario: Start a later user turn
- **WHEN** a later turn begins after the prior one ended
- **THEN** automatic Float presentation is enabled for that turn

#### Scenario: Switch conversations
- **WHEN** the learner opens another conversation
- **THEN** old activity/collapse state does not appear in the new conversation

#### Scenario: Reopen the current Float explicitly
- **WHEN** the learner activates the collapsed Float's small control
- **THEN** current progress reopens without changing the selected middle page or starting another task

### Requirement: Agent sending is single-flight and session-bound
The composer SHALL remain editable during execution. Its per-submission network request SHALL be single-flight/idempotent, while distinct new messages MAY be accepted into the pending queue or explicit interrupt-and-send path. Same-conversation provider execution SHALL remain single-worker. Click/Enter SHALL share acceptance identity/gating; duplicate input events SHALL NOT create duplicate work. Conversation changes SHALL invalidate obsolete callbacks and approvals without moving messages into another conversation. Unknown progress SHALL NOT release permission to run a second task.

#### Scenario: Type during a running turn
- **WHEN** a turn is active and the learner submits a distinct new message
- **THEN** the composer stays usable and the configured queue or explicit interruption behavior applies without simultaneous provider execution

#### Scenario: Submit twice before receiving a turn identifier
- **WHEN** Send and Enter occur for one submission before acknowledgement
- **THEN** only one accepted message and at most one corresponding execution result

#### Scenario: Switch sessions with pending runtime state
- **WHEN** the learner switches conversation during a pending request/activity/approval
- **THEN** stale callbacks cannot render or act in the newly selected conversation and messages remain owned by their original conversation

#### Scenario: Progress polling fails before a terminal response
- **WHEN** the progress endpoint is temporarily unavailable during execution
- **THEN** active-turn identity remains, pending messages may be retained, and no pending task dispatches merely because polling failed

## ADDED Requirements

### Requirement: Failed and uncertain user messages remain recoverable
The UI SHALL preserve outgoing text/context before clearing the composer. A rejected/unacknowledged send SHALL remain visibly recoverable across refresh without overwriting a newer draft. Accepted provider failures SHALL preserve the user's message in canonical history and link available failure/partial-output information. Unknown acceptance SHALL be visibly distinct from rejection and SHALL reconcile the same identity before resend. Retrying SHALL be explicit; the original message SHALL NOT disappear or be silently duplicated.

#### Scenario: Send request is rejected
- **WHEN** the message POST fails before confirmed acceptance
- **THEN** original text remains visible with retry/edit recovery and survives refresh instead of being swallowed

#### Scenario: Accepted work fails and history reloads
- **WHEN** the provider fails for an accepted message and the conversation is reopened
- **THEN** original user text and failed status remain visible even with no assistant answer

### Requirement: Running-send preference and pending controls are explicit
Running-send default SHALL be queue, configurable through existing workspace settings. Queue and interrupt-and-send SHALL remain explicit choices. Pending entries SHALL show retained text/order/status with edit/remove/continue controls appropriate to state. Changing the preference SHALL affect future submissions only. Failures and priority interruption SHALL visibly pause the retained older queue rather than silently continuing it.

#### Scenario: Change the default behavior
- **WHEN** the learner changes running-send behavior in settings
- **THEN** later submissions use it, the preference survives normal browser reopening, and already accepted/running work is unchanged

#### Scenario: Priority message leaves the older queue paused
- **WHEN** D interrupts A while B/C are queued and D finishes
- **THEN** the UI still shows B/C paused and requires explicit continuation instead of resuming A or automatically dispatching B

### Requirement: Tool and approval controls report real effects
A Tool Call Card SHALL show a semantic action/state/outcome, known completed/failed impact and folded redacted diagnostics. Recovery controls SHALL correspond to actual backend-supported actions. Unsupported selective retry SHALL NOT be presented as working. Existing governed Paper-reset and rollback confirmations SHALL show their exact impact and remain bound to the intended workspace/conversation/message/revision; cancellation or stale approval SHALL perform no write.

#### Scenario: Partly committed operation fails
- **WHEN** a Tool has known completed effects and a failed part
- **THEN** its card distinguishes those effects and offers only supported scoped recovery or explicit new/read-only assistance, never an automatic replay of successful writes
