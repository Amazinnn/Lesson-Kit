## REMOVED Requirements

### Requirement: Paper update approval pauses conversation dispatch

**Reason**: The owner explicitly cancels project approvals in Q098/S008.
**Migration**: Use direct-project-actions. Validate the actual operation input, reconcile legacy pending state once and remove approval-driven UI and dispatch pauses.

## MODIFIED Requirements

### Requirement: Interrupt-and-send waits for the old turn to stop

An explicit interrupt-and-send SHALL durably accept its message and bind its cancellation request to the running turn that was current at acceptance. It SHALL start the interrupt message directly only after that captured turn's provider worker reaches an authoritative terminal state and releases ownership. The interrupt SHALL NOT be inserted into the ordinary queue, depend on queue continuation, or fall back to queue routing; waiting for stop confirmation is an independent handoff state. A stop request, timeout, or missing progress response alone SHALL NOT authorize concurrent execution. The bridge SHALL preserve already completed effects and SHALL NOT resume or roll back the old task automatically. Messages queued before the interrupt SHALL remain paused after the interrupt message, including when it succeeds. While an interrupt message is waiting for stop confirmation, another distinct interrupt submission SHALL be rejected as a conflict without discarding the accepted one.


Project approval SHALL be retired. Any persisted legacy pending approval SHALL be reconciled under direct-project-actions and SHALL NOT block dispatch solely for approval. All unrelated identity, single-flight, stop-handoff and context constraints SHALL remain applicable.

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

- **WHEN** a request encounters a legacy pending approval state
- **THEN** that state is reconciled without an approval gate and the requested operation follows normal identity, ownership and concurrency rules without approval-driven blocking

#### Scenario: Approval blocks interrupt acceptance

- **WHEN** a request encounters a legacy pending approval state
- **THEN** that state is reconciled without an approval gate and the requested operation follows normal identity, ownership and concurrency rules without approval-driven blocking

#### Scenario: Service restarts during an interrupt handoff

- **WHEN** the service restarts before an accepted interrupt message begins and cannot safely complete the captured old-worker handoff
- **THEN** it retains the accepted message as interrupted or failed for explicit recovery, does not convert it to queued work, does not run it automatically, and keeps any ordinary queued messages paused


### Requirement: Pending messages can be revised or removed before execution

A pending message SHALL retain its current text and captured context in its accepted turn artifact. The learner MAY edit or remove it only while it has not begun provider execution. Each successful edit SHALL increment that message's revision; edit and removal requests SHALL include the expected revision and SHALL conflict without mutation when the message has started, been removed, or changed since it was read. Removal SHALL retain a cancelled accepted-turn history entry. Editing SHALL NOT replace the originally captured context with the currently selected page context.

The learner SHALL also be able to reorder the ordinary queued messages or send one of them now. Reorder SHALL atomically compare the complete expected pending order with the current order under the same dispatch ownership lock, accept only a permutation of exactly the queued entries, and preserve message identities, text and contexts. A stale order or an ineligible entry SHALL conflict without partial mutation.

Send-now SHALL atomically validate the target queued message and expected revision, remove it from the ordinary queue and use the direct interrupt-and-send path. It SHALL preserve that accepted turn identity, its current edited text and original captured context, rather than creating a duplicate turn. Existing queued peers SHALL retain their relative order and remain paused. Repetition for the same already-promoted turn SHALL return the same accepted result without cancelling a later running turn or dispatching twice. Ordinary submission-identity reconciliation SHALL NOT itself promote an accepted message.


Project approval SHALL be retired. Any persisted legacy pending approval SHALL be reconciled under direct-project-actions and SHALL NOT block dispatch solely for approval. All unrelated identity, single-flight, stop-handoff and context constraints SHALL remain applicable.

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

- **WHEN** a request encounters a legacy pending approval state
- **THEN** that state is reconciled without an approval gate and the requested operation follows normal identity, ownership and concurrency rules without approval-driven blocking

