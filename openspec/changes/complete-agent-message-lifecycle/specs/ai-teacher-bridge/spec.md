## ADDED Requirements

### Requirement: Accepted user messages survive unsuccessful turns
The bridge SHALL durably record a submitted user message, its stable submission identity and captured context before acknowledging acceptance or launching a provider. History SHALL include accepted queued/running/failed/cancelled messages independently of a successful assistant exchange. Repeating the same submission identity and payload SHALL return the same accepted message without duplicate execution; conflicting payload reuse SHALL fail explicitly. Legacy successful transcripts SHALL remain readable without duplicate user entries. Missing text from historical legacy failures SHALL NOT be fabricated.

#### Scenario: Provider fails before producing an answer
- **WHEN** an accepted message encounters provider startup or runtime failure
- **THEN** reopening or refreshing history still shows the original user text with its failed turn and available public output/diagnostics

#### Scenario: Acceptance response is lost
- **WHEN** the server accepted a message but the browser did not receive the response and retries its same identity
- **THEN** the bridge resolves to the same message/turn and does not start another execution

#### Scenario: Read old successful history
- **WHEN** a conversation with legacy transcript exchanges is opened after the change
- **THEN** each original user/assistant exchange remains readable once and no missing failed-message text is invented

### Requirement: Running messages use a single-worker conversation queue
A conversation SHALL have at most one executing provider turn. Further accepted messages SHALL enter an ordered pending queue unless explicitly submitted as interrupt-and-send. Queued messages SHALL preserve submission-time context, remain inspectable/editable/removable until execution begins, and survive page navigation/refresh. A successful ordinary turn MAY dispatch the next queued message; a failed or unexpectedly interrupted turn SHALL pause and retain the queue until explicit continuation. Service recovery SHALL pause retained work after an unowned running turn rather than silently launching it. Progress-read failure alone SHALL NOT count as a terminal provider failure.

#### Scenario: Queue while another turn runs
- **WHEN** A runs and the user submits B and C under queue behavior
- **THEN** B/C are visibly accepted in order and no provider for them starts until the prior turn finishes successfully and queue dispatch is allowed

#### Scenario: Failure pauses later messages
- **WHEN** A fails while B/C are pending
- **THEN** B/C retain their text/order/context but do not execute until the user explicitly resumes or changes them

#### Scenario: Page changes after enqueue
- **WHEN** B is queued from a practice page and the user opens a graph before B begins
- **THEN** B retains its submitted practice-page context rather than silently using the graph context

#### Scenario: Recover after service interruption
- **WHEN** the local service restarts with accepted pending messages and an interrupted running turn
- **THEN** the messages remain visible, the interrupted turn is reported honestly, and pending dispatch remains paused

### Requirement: Interrupt-and-send waits for the old turn to stop
An explicit interrupt-and-send SHALL retain the priority message, request cancellation of the current turn and wait for authoritative termination before starting the priority message. It SHALL preserve already completed effects and SHALL NOT resume the old task or roll it back automatically. Preexisting queued messages SHALL remain paused after the priority message, including if it succeeds. Failure to confirm cancellation SHALL retain the priority message without launching it concurrently.

#### Scenario: A running task with older queued messages is interrupted by D
- **WHEN** A is running, B/C are queued and the user explicitly interrupts with D
- **THEN** A stops before D starts, A never resumes automatically, and B/C remain retained and paused after D

#### Scenario: Stop acknowledgement is unavailable
- **WHEN** cancellation of A cannot be confirmed
- **THEN** D stays visibly waiting for stop confirmation and no second executing turn is launched

### Requirement: Recovery does not replay successful effects blindly
Retry of an accepted failed message SHALL be an explicit linked attempt with preserved original history. Unknown submission status SHALL first reconcile by its original identity. A UI tool-recovery operation SHALL execute only a backend-supported scoped action; it SHALL NOT blindly replay a provider command whose completed effects are unknown.

#### Scenario: A tool partly succeeds before failure
- **WHEN** recovery is offered for a turn with committed effects and a failed operation
- **THEN** known completed effects remain visible and recovery targets only a supported safe action or explicit new Agent instruction, not automatic full-write replay
