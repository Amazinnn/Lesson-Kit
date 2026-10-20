## MODIFIED Requirements

### Requirement: Serialized turn execution

A conversation SHALL run at most one provider turn at a time. A new message accepted with the queue action during an active turn SHALL be retained with its submission-time context, appended by default in FIFO order. Explicit accepted reorder operations SHALL define the shared persisted display and dispatch order. Interrupt-and-send SHALL use a separate stop-and-handoff path and SHALL NOT enter the ordinary queue. Successful ordinary turns SHALL allow the next queued message to run without relying on an open browser tab. A failed, cancelled without an interrupt intent, or unexpectedly interrupted turn SHALL pause retained messages until explicit continuation. Service recovery SHALL report an unowned running turn as interrupted or failed and pause all retained work without dispatching it. A progress-read failure alone SHALL NOT change turn or queue status. Turn events SHALL have monotonically increasing sequence numbers, and cancellation SHALL target the captured running turn.

#### Scenario: Send while a turn is running

- **WHEN** turn A is running and messages B and C are accepted with the queue action
- **THEN** B and C remain visible in default FIFO order with their captured contexts, and neither provider starts before A reaches a terminal status

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

#### Scenario: Dispatch after an explicit reorder

- **WHEN** A completes and the confirmed queued order has been changed from B/C to C/B
- **THEN** C starts after A releases provider ownership, then B may start after C succeeds; browser polling is not required

#### Scenario: Legacy conversation order

- **WHEN** a conversation has queued turns but no explicit queue-order field
- **THEN** reads preserve the existing numeric-turn FIFO order without rewriting unrelated artifacts; a later accepted queue mutation persists the explicit order


### Requirement: Interrupt-and-send waits for the old turn to stop

An explicit interrupt-and-send SHALL durably accept its message and bind its cancellation request to the running turn that was current at acceptance. It SHALL start the interrupt message directly only after that captured turn's provider worker reaches an authoritative terminal state and releases ownership. The interrupt SHALL NOT be inserted into the ordinary queue, depend on queue continuation, or fall back to queue routing; waiting for stop confirmation is an independent handoff state. A stop request, timeout, or missing progress response alone SHALL NOT authorize concurrent execution. The bridge SHALL preserve already completed effects and SHALL NOT resume or roll back the old task automatically. Messages queued before the interrupt SHALL remain paused after the interrupt message, including when it succeeds. While an interrupt message is waiting for stop confirmation, another distinct interrupt submission SHALL be rejected as a conflict without discarding the accepted one.

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

#### Scenario: Interrupt when no queue exists

- **WHEN** A runs, no queued messages exist, and D is accepted with interrupt-and-send
- **THEN** cancellation targets A and D runs directly after A is authoritatively terminal and releases ownership; no ordinary queue is created or resumed

#### Scenario: Interrupt when no provider is running

- **WHEN** D is submitted with interrupt-and-send while no provider owns the conversation and no approval or other handoff blocks acceptance
- **THEN** D starts directly without an artificial queue step or explicit continue action, and any pre-existing paused queued messages remain paused

#### Scenario: Approval blocks interrupt acceptance

- **WHEN** a new interrupt message is submitted while a Paper approval is pending
- **THEN** the service rejects it with a conflict before accepting or enqueuing it, and no provider or Paper operation runs


#### Scenario: Service restarts during an interrupt handoff

- **WHEN** the service restarts before an accepted interrupt message begins and cannot safely complete the captured old-worker handoff
- **THEN** it retains the accepted message as interrupted or failed for explicit recovery, does not convert it to queued work, does not run it automatically, and keeps any ordinary queued messages paused

### Requirement: Pending messages can be revised or removed before execution

A pending message SHALL retain its current text and captured context in its accepted turn artifact. The learner MAY edit or remove it only while it has not begun provider execution. Each successful edit SHALL increment that message's revision; edit and removal requests SHALL include the expected revision and SHALL conflict without mutation when the message has started, been removed, or changed since it was read. Removal SHALL retain a cancelled accepted-turn history entry. Editing SHALL NOT replace the originally captured context with the currently selected page context.

The learner SHALL also be able to reorder the ordinary queued messages or send one of them now. Reorder SHALL atomically compare the complete expected pending order with the current order under the same dispatch ownership lock, accept only a permutation of exactly the queued entries, and preserve message identities, text and contexts. A stale order or an ineligible entry SHALL conflict without partial mutation.

Send-now SHALL atomically validate the target queued message and expected revision, remove it from the ordinary queue and use the direct interrupt-and-send path. It SHALL preserve that accepted turn identity, its current edited text and original captured context, rather than creating a duplicate turn. Existing queued peers SHALL retain their relative order and remain paused. Repetition for the same already-promoted turn SHALL return the same accepted result without cancelling a later running turn or dispatching twice. Ordinary submission-identity reconciliation SHALL NOT itself promote an accepted message.


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

- **WHEN** a message is accepted with the queue action while older messages remain paused
- **THEN** the new message remains retained with them and does not implicitly continue the queue

#### Scenario: Reorder queued messages

- **WHEN** the learner submits an expected order B/C and new order C/B while both remain queued
- **THEN** the service commits C/B as both display and execution order without changing their text, identity or original context

#### Scenario: Reorder races with dispatch or another queue mutation

- **WHEN** an entry starts, a queued entry is added/removed, or another reorder wins before a stale reorder is committed
- **THEN** the stale operation returns a conflict, leaves the current order unchanged and does not mutate the executing turn

#### Scenario: Promote an edited queued message

- **WHEN** queued C has been edited and send-now is accepted at its current revision while A runs and B is queued
- **THEN** C is removed from ordinary queue order, A is captured for cancellation, C runs once after A releases ownership using its existing identity, edited text and original context, and B remains paused

#### Scenario: Send-now races with dispatch

- **WHEN** C has not already been promoted by this operation and ordinary dispatch starts C or its revision changes before send-now is accepted
- **THEN** the operation conflicts without cancelling another turn, duplicating C or removing a different queued message

#### Scenario: Repeat send-now after promotion

- **WHEN** the same send-now request for C is repeated after C was already promoted or started
- **THEN** the service returns C's existing result without another execution or cancellation target

#### Scenario: Send-now is blocked

- **WHEN** a pending approval or a different stop handoff blocks send-now
- **THEN** the request conflicts and the original message stays queued with its original text, context and order


### Requirement: Paper update approval pauses conversation dispatch

The Bridge SHALL retain an Agent-proposed existing-Paper update and its approval state in the existing conversation/turn artifacts without applying it. Before the proposing provider turn releases ownership to the next queued message, the Bridge SHALL persist the pending approval and pause that conversation's dispatch. Waiting for learner approval SHALL NOT keep a provider task running. While approval is pending, messages explicitly submitted with queue MAY be accepted into the paused queue with their captured context. Interrupt-and-send and send-now SHALL be rejected without creating or rerouting a queued item; queue continuation SHALL NOT bypass the decision.

Only the page's explicit learner-approval operation SHALL apply this proposed update through the existing Paper preview/confirmation and update rules. A stale impact SHALL cause no write and require refreshed impact plus another learner click. Cancellation SHALL cause no Paper write. Both approval and cancellation SHALL retain older queued messages and leave continuation manual. Repeated approval attempts SHALL NOT apply the update or reset progress twice.

Pending approval SHALL survive page reload/reopen and service recovery with dispatch paused and no automatic approval or replay. Workspace, conversation, proposing turn, target Paper and operation revision SHALL scope each decision. This integration SHALL NOT alter historical attempts/ratings, question entities, unrelated Papers or the existing direct manual CLI contract.

#### Scenario: A proposes a Paper update with B/C queued
- **WHEN** provider turn A completes with a Paper update requiring approval while B/C are queued
- **THEN** its pending approval is persisted and dispatch is paused before ownership handoff; B/C do not start even with the browser closed

#### Scenario: Approval is resolved
- **WHEN** the learner approves or cancels the pending operation
- **THEN** only a current valid approval may write the target Paper, B/C remain retained and paused, and explicit continuation is required

#### Scenario: New work is accepted during approval
- **WHEN** another message is accepted with queue while the conversation has a pending Paper approval
- **THEN** its text and submission context are retained without provider dispatch or implicit resolution of the approval

#### Scenario: Recover a pending operation
- **WHEN** the service recovers a conversation with a persisted pending Paper approval
- **THEN** the operation remains pending, the queue stays paused, and neither the Paper update nor a queued provider starts automatically

#### Scenario: Interrupt is refused during approval

- **WHEN** the learner submits interrupt-and-send or send-now while a Paper approval is pending
- **THEN** the operation conflicts without provider dispatch, Paper writes, or conversion of the interrupt into queued work; an existing queued send-now target remains unchanged
