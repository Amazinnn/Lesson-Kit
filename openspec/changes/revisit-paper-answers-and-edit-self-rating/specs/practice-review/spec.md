## RENAMED Requirements

- FROM: `### Requirement: Review the immediately previous ordinary problem`
- TO: `### Requirement: Review completed ordinary problems throughout a Paper run`

## MODIFIED Requirements

### Requirement: Review completed ordinary problems throughout a Paper run

For ordinary problems with a submitted answer or a recorded `??` state in the selected Paper's same Practice Run, the practice page SHALL allow repeated backward and forward review through all such items, without a one-item or visit-count limit. The view SHALL show the problem, learner answer or `??`, available verdict and existing self-rating. Reference answers and solutions SHALL be collapsed on every entry, including re-entry to the same reviewed problem, and SHALL appear only after an explicit reveal action. An unavailable verdict SHALL be stated as unavailable rather than inferred from self-rating. Browser-held unconfirmed submission state MAY be shown with an explicit unconfirmed label and SHALL NOT be represented as a durably saved Attempt. Original answering and skip controls SHALL NOT mutate the reviewed submission.

#### Scenario: Review after advancing

- **WHEN** the browser has submitted an answer or marked the ordinary problem `??` and advanced to the next unanswered ordinary problem
- **THEN** `?????` is available and shows that answer or state with any available verdict
- **AND** reference answers and solutions remain collapsed

#### Scenario: Review while the attempt write is unconfirmed

- **WHEN** the browser holds a submitted answer, its write remains unconfirmed, and practice has advanced
- **THEN** review still shows the browser-held answer explicitly labelled unconfirmed
- **AND** it does not imply durable persistence or allow a self-rating write against an unconfirmed Attempt

#### Scenario: Return to the current problem

- **WHEN** the learner activates `?????` from any reviewed item
- **THEN** the selected execution's current problem is shown with its unsent text or selected choices restored

#### Scenario: Review more than one earlier problem repeatedly

- **GIVEN** at least four ordinary problems have recorded answers in one execution
- **WHEN** the learner repeatedly navigates backward to the first and forward to the last recorded problem
- **THEN** all are reachable without a visit-count limit and boundary controls are disabled rather than wrapping
- **AND** each entry hides reference answers and solutions even if they were revealed on an earlier visit

#### Scenario: Explicit reveal and unavailable verdict

- **WHEN** the learner opens a reviewed problem without a recorded verdict
- **THEN** it shows the learner answer and a truthful unavailable-verdict state without revealing the answer key
- **AND** an explicit reveal action may show available reference material without creating learning evidence

#### Scenario: Restore persisted review after reload or Paper switching

- **WHEN** the learner reloads or leaves and resumes the same Paper execution
- **THEN** its persisted reviewed submissions remain accessible independently of other Papers
- **AND** missing original submissions are not fabricated from the current answer key

### Requirement: Review is an overlay, not practice navigation

Review browsing and answer reveal SHALL NOT move the durable practice cursor, alter completion state, create an Attempt, write feedback, or reopen an original answer for submission. Only an explicit self-rating save under this capability MAY change the reviewed submission's linked self-rating and its learning effects. Flash-card previous/next navigation SHALL retain its existing cursor-based behavior. An accessible completed execution SHALL remain reviewable without being restarted or requiring a current unanswered problem.

#### Scenario: Review leaves progress unchanged

- **WHEN** the learner opens, navigates, reveals reference material and closes review without explicitly saving a self-rating
- **THEN** durable cursor, attempts, feedback and completion state remain unchanged

#### Scenario: Review a completed execution

- **WHEN** the learner opens review for an accessible completed Paper execution
- **THEN** recorded items remain reviewable without restarting it or creating an unanswered item

### Requirement: Agent context follows the visible reviewed problem

While review is open, a new Agent turn from the practice page SHALL identify the visible reviewed problem and its submitted answer as focused context. Navigating among reviewed items SHALL update that focus without moving durable practice progress. Returning to the current problem SHALL restore ordinary current-problem context. Previously accepted messages SHALL retain their submission-time context.

#### Scenario: Ask the Agent while reviewing

- **WHEN** the learner sends an Agent message while a reviewed result is visible
- **THEN** that reviewed problem and its submitted answer are the focused context without moving practice progress

#### Scenario: Navigate after sending

- **WHEN** the learner sends a message while reviewing A and then views B
- **THEN** a new message uses B while the accepted message keeps A's context

## ADDED Requirements

### Requirement: Explicit self-rating editing for a reviewed submission

When self-rating is enabled for the execution, a durably saved reviewed submission SHALL allow editing its linked 1?5 self-rating and optional feedback note, including an earlier submission followed by later learning activity. Saving SHALL preserve its original learner answer, objective verdict and Attempt identity. A changed rating SHALL replace that submission's effective rating contribution rather than accumulate a duplicate; later learning activities and their records SHALL be preserved and learning projections and schedules SHALL reflect the corrected contribution consistently. Cancellation SHALL write nothing. The save SHALL use exact target identity, concurrency validation and idempotent request handling. Failed saves SHALL preserve unsaved edits and report failure truthfully. Disabling self-rating SHALL retain the execution's existing preference behavior.

#### Scenario: Edit an existing self-rating

- **WHEN** the learner explicitly saves a different valid rating for a reviewed submission
- **THEN** the linked effective rating and learning effects are updated once, without a new Attempt or a changed answer, verdict, cursor or completion state

#### Scenario: Preserve later learning activities

- **GIVEN** a reviewed submission has a self-rating and later learning activities affect the same problem or knowledge points
- **WHEN** that earlier self-rating is changed
- **THEN** later records and contributions are preserved, the former rating contribution is not duplicated, and projections and schedules consistently incorporate the change

#### Scenario: Cancel or reject invalid input

- **WHEN** the learner cancels editing or tries to save a rating outside the existing integer 1?5 scale
- **THEN** no learning records are changed and invalid input receives a readable error

#### Scenario: Retry a lost response

- **WHEN** an identical save is retried after its response is lost
- **THEN** it returns the same effective result without duplicating feedback contributions or advancing progress

#### Scenario: Stale target and delayed response

- **WHEN** the reviewed target has been changed or invalidated before save, or its response arrives after switching Papers
- **THEN** a stale write is rejected without changes and a delayed response cannot overwrite the other Paper's current state or draft

#### Scenario: Save failure retains the editor

- **WHEN** a self-rating save fails
- **THEN** the edited rating and note remain available for retry or cancellation and the UI does not claim success
