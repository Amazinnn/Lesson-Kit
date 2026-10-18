## ADDED Requirements

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
