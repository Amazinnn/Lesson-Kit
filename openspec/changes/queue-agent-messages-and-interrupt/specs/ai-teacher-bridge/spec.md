## MODIFIED Requirements

### Requirement: Serialized turn execution

A conversation SHALL run at most one provider turn at a time. A new accepted message submitted during an active turn SHALL be retained in FIFO order with its submission-time context. Successful ordinary turns SHALL allow the next queued message to run without relying on an open browser tab. A failed, cancelled without an interrupt intent, or unexpectedly interrupted turn SHALL pause retained messages until explicit continuation. Service recovery SHALL report an unowned running turn as interrupted or failed and pause all retained work without dispatching it. A progress-read failure alone SHALL NOT change turn or queue status. Turn events SHALL have monotonically increasing sequence numbers, and cancellation SHALL target the captured running turn.

#### Scenario: Send while a turn is running

- **WHEN** turn A is running and messages B and C are accepted with the queue action
- **THEN** B and C remain visible in FIFO order with their captured contexts, and neither provider starts before A reaches a terminal status

#### Scenario: Continue ordinary work after success

- **WHEN** A completes successfully while B and C are queued and the queue is not paused
- **THEN** B starts after A's provider worker has returned, and C starts after B succeeds without requiring browser polling or navigation

#### Scenario: Failure pauses later messages

- **WHEN** A fails or is cancelled without an accepted interrupt message while B and C are queued
- **THEN** B and C remain accepted and paused until the learner explicitly continues the queue

#### Scenario: Pause survives service recovery

- **WHEN** the service reads a conversation containing an unowned running turn and queued messages
- **THEN** it marks the running turn interrupted or failed, retains the messages, and leaves dispatch paused

#### Scenario: Progress cannot be read

- **WHEN** a progress request fails while the provider turn has no authoritative terminal status
- **THEN** the turn remains active and no later provider turn starts

### Requirement: Accepted Agent messages survive failed turns

When a turn request includes a `submission_id`, the bridge SHALL persist the originally accepted user text, the current user text, the original captured context, and stable task fields in the existing turn artifact before provider dispatch. Repeating that identity with the same originally submitted text and task fields SHALL return the same turn without changing its current text, queue position, context, or dispatch state. Reusing the identity with changed task fields SHALL return a conflict. Delivery action is routing metadata and SHALL NOT change the submitted task identity. Editing a queued message SHALL change only its current text and queue revision; it SHALL preserve the original identity and context. An explicit retry of a failed edited message SHALL use its current text and original captured context. Requests without `submission_id` SHALL retain their existing behavior.

Conversation history SHALL include accepted turn messages independently of successful transcript exchanges. A turn already represented by a legacy successful transcript SHALL appear exactly once. Failed turns SHALL expose only actual public partial output and their truthful terminal status; history SHALL NOT invent missing user text, assistant output, or legacy failures.

#### Scenario: Provider fails after acceptance

- **WHEN** the provider fails before producing an answer for an accepted turn
- **THEN** reopening history shows the original accepted user text and failed status, with any actual public partial output

#### Scenario: Acceptance response is lost and retried

- **WHEN** the client repeats the same `submission_id` and submitted task fields after an unknown response
- **THEN** the bridge returns the original turn without dispatching a second provider, even if that pending message has since been edited

#### Scenario: Same identity is reused with changed fields

- **WHEN** a request reuses a stored `submission_id` with different text as originally accepted or different submitted task fields
- **THEN** the bridge returns a conflict and leaves the accepted turn unchanged

#### Scenario: Delivery action changes before retry

- **WHEN** the same accepted submission is reconciled with a different queue or interrupt action
- **THEN** the bridge returns the original turn and does not change its existing routing or execution state

#### Scenario: Retry an edited failed message

- **WHEN** a queued message is edited, later fails after execution, and the learner explicitly retries it
- **THEN** the new linked turn uses the edited text and the original captured context

#### Scenario: Server enrichment changes before duplicate resolution

- **WHEN** the same submitted task fields are retried after server-derived page enrichment has changed
- **THEN** the bridge returns the original turn and retains its originally captured context

#### Scenario: Read legacy successful history

- **WHEN** a conversation contains successful transcript exchanges created before this change
- **THEN** each exchange remains readable once and no missing failed-message text is synthesized

### Requirement: Interrupt-and-send waits for the old turn to stop

An explicit interrupt-and-send SHALL durably accept its message and bind its cancellation request to the running turn that was current at acceptance. It SHALL start the interrupt message only after that captured turn's provider worker reaches an authoritative terminal state. A stop request, timeout, or missing progress response alone SHALL NOT authorize concurrent execution. The bridge SHALL preserve already completed effects and SHALL NOT resume or roll back the old task automatically. Messages queued before the interrupt SHALL remain paused after the interrupt message, including when it succeeds. While an interrupt message is waiting for stop confirmation, another distinct interrupt submission SHALL be rejected as a conflict without discarding the accepted one.

#### Scenario: Interrupt A with queued B/C and send D

- **WHEN** A is running, B and C are queued, and D is accepted with interrupt-and-send
- **THEN** D waits for A's actual terminal acknowledgement, then runs once, while B and C remain retained and paused after D

#### Scenario: A finishes as cancellation races

- **WHEN** D is accepted while A is running but A reaches a normal terminal result before its cancellation takes effect
- **THEN** D still runs after A, and B and C remain paused

#### Scenario: Stop acknowledgement is unavailable

- **WHEN** A has not reached an authoritative terminal state after D requests cancellation
- **THEN** D remains visibly waiting for stop confirmation and no second provider runs

#### Scenario: A second interrupt is submitted

- **WHEN** a distinct interrupt message is submitted while an earlier interrupt message is waiting for A to stop
- **THEN** the new submission receives a conflict and the earlier accepted interrupt message remains intact

### Requirement: Pending messages can be revised or removed before execution

A pending message SHALL retain its current text and captured context in its accepted turn artifact. The learner MAY edit or remove it only while it has not begun provider execution. Each successful edit SHALL increment that message's revision; edit and removal requests SHALL include the expected revision and SHALL conflict without mutation when the message has started, been removed, or changed since it was read. Removal SHALL retain a cancelled accepted-turn history entry. Editing SHALL NOT replace the originally captured context with the currently selected page context.

#### Scenario: Edit a queued message

- **WHEN** the learner edits a queued message using its current revision
- **THEN** the current text and revision change while its accepted identity, original submitted fields, queue position, and captured context remain unchanged

#### Scenario: Remove a queued message

- **WHEN** the learner removes a queued message using its current revision
- **THEN** it is retained in history as cancelled and is not sent to a provider

#### Scenario: Edit races with queue dispatch

- **WHEN** an edit or removal races with the queued message starting
- **THEN** the ownership lock makes one operation win; a stale or already-running mutation returns a conflict and does not change the executing message

#### Scenario: Resume a paused queue explicitly

- **WHEN** the learner continues a paused queue while no provider turn is running
- **THEN** the earliest eligible retained message starts, then later messages may continue after success

#### Scenario: New work does not resume an old queue

- **WHEN** a message is accepted while older messages remain paused
- **THEN** the new message remains retained with them and does not implicitly continue the queue
