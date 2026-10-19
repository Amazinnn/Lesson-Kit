# practice-review Specification

## Purpose

Let learners freely navigate ordinary Paper items before and after explicit final submission, disclose results according to the run's Answer Reveal Timing, and overwrite linked self-ratings without replaying learning effects. Navigation changes no answer conclusion. Flash-card-specific navigation retains its existing behavior.
## Requirements
### Requirement: Agent context follows the visible reviewed problem

A new Agent turn from ordinary Paper practice SHALL use the visible problem and that run's answer or draft as focused context, whether answering, browsing a locked item, or viewing a completed answer sheet. Previously accepted messages SHALL retain submission-time context. Changing the visible item SHALL NOT submit an answer or create learning evidence.

#### Scenario: Ask the Agent while reviewing
- **WHEN** the learner sends an Agent message while a reviewed result is visible
- **THEN** that problem and submitted answer are focused context without another submission

#### Scenario: Navigate after sending
- **WHEN** the learner sends a message while viewing A and then views B
- **THEN** a new message uses B while the accepted message keeps A's context

### Requirement: Explicit self-rating editing for a reviewed submission

When self-rating is enabled for the selected Paper execution, a durably saved reviewed submission in that same run SHALL allow editing its linked 1–5 self-rating and optional feedback note, including an earlier item in the run. Following the owner's 2026-10-17 decision, saving an edit SHALL overwrite that submission's previous rating and note in place, preserving its learner answer, objective verdict and Attempt identity. It SHALL NOT append another feedback event or Attempt, reapply signals/current-state/schedule effects, replay global learning history, or modify another Paper or run. The first rating, when none exists, SHALL retain the existing rating flow. Cancellation SHALL write nothing. Saves SHALL validate the exact execution/Attempt identity and current expected rating, and retry safely. Failed saves SHALL retain edits and report failure truthfully. Disabled self-rating SHALL retain the execution's existing preference behavior.

#### Scenario: Edit an existing self-rating

- **WHEN** the learner explicitly saves a different valid rating for a reviewed submission
- **THEN** its existing rating and note are overwritten without a new feedback event or Attempt and without changing the answer, verdict, cursor, completion state, signals or schedule

#### Scenario: Repeated edits remain scoped to this Paper run

- **GIVEN** an earlier item in the selected Paper run has a saved self-rating and the problem also has records in another run
- **WHEN** the learner edits the earlier item's rating and note more than once
- **THEN** the same linked feedback record contains the last saved values, other runs remain unchanged, and no additional evidence or scheduling effects are produced

#### Scenario: Cancel or reject invalid input

- **WHEN** the learner cancels editing or tries to save a rating outside the existing integer 1–5 scale
- **THEN** no learning records are changed and invalid input receives a readable error

#### Scenario: Retry a lost response

- **WHEN** an identical save is retried after its response is lost
- **THEN** it returns the same effective result without duplicating feedback contributions or advancing progress

#### Scenario: Stale target and delayed response

- **WHEN** the reviewed target has changed or been invalidated before the save is applied
- **THEN** the stale write is rejected without changes
- **AND** an explicit save initiated for A may finish after switching to B, but it updates only the original A target and its delayed response cannot overwrite B's state or draft

#### Scenario: Save failure retains the editor

- **WHEN** a self-rating save fails
- **THEN** the edited rating and note remain available for retry or cancellation and the UI does not claim success

### Requirement: Free navigation throughout a Paper

An ordinary-problem Paper SHALL expose previous, next, and explicit `不会` controls. Previous/next and numbered status dots SHALL reach every item, including unanswered and locked items, without a visit-count limit. First previous and last next SHALL be disabled without wrapping or submitting the Paper. Navigation SHALL preserve input and SHALL NOT submit, mark stuck, rate, or complete an item. Locked items SHALL remain viewable without accepting another answer or a new stuck mark. Flash-card-specific behavior SHALL remain outside this ordinary-problem replacement.

#### Scenario: Traverse the whole Paper repeatedly
- **GIVEN** a Paper has at least five items with mixed unanswered, answered and stuck states
- **WHEN** the learner moves from the fifth to the first and back, including dot jumps
- **THEN** all items remain reachable and answer states remain unchanged

#### Scenario: Leave an unsubmitted item
- **WHEN** the learner types text or checks several options and navigates away without submitting
- **THEN** input is preserved without navigation creating a verdict or Attempt

#### Scenario: Navigate a completed answer sheet
- **WHEN** the learner opens the completed run's answer sheet
- **THEN** every item is viewable with its recorded answer/state and truthful available verdict, without reopening the run

### Requirement: Mode-specific answer reveal and locking

Answer Reveal Timing SHALL be selected before a new run and remain fixed for it. In per-item mode, single-choice or yes/no selection SHALL submit the answer; multiple-choice and text items SHALL instead expose `提交答案` and submit only on activation. Successful submission SHALL lock the answer and automatically expand available verdict, reference answer and solution. Text and keyless items SHALL NOT receive invented verdicts. Explicit `不会` SHALL reveal available reference material and lock the item as stuck. Unconfirmed writes SHALL be labelled truthfully and remain recoverable; the UI SHALL NOT claim durable success before confirmation.

In whole-Paper mode, inputs SHALL auto-save and remain editable until final submission, without per-item submit controls or premature verdict/reference reveal. Explicit `不会` SHALL reveal reference material and set a revisable stuck mark. Entering a new answer SHALL clear that mark while preserving that reference material was viewed. Navigation SHALL not clear a mark. An already disclosed answer SHALL NOT be treated as unseen.

#### Scenario: Submit a single-choice item
- **WHEN** the learner selects an option in per-item mode
- **THEN** the answer is submitted and, after success, results and reference material appear with the answer locked

#### Scenario: Submit multiple-choice or text
- **WHEN** input changes without activating submit in per-item mode
- **THEN** it remains editable and reference material stays hidden
- **AND** activating submit submits the input, locks it after success, and expands reference material

#### Scenario: Mark stuck in each mode
- **WHEN** the learner activates `不会`
- **THEN** available reference material is shown immediately
- **AND** per-item mode locks the stuck state while whole-Paper mode allows a new answer to clear it before final submission

#### Scenario: Reference material is unavailable
- **WHEN** an item has no recorded answer, solution or usable key
- **THEN** absent material and unavailable verdict are stated honestly rather than generated or inferred from self-rating

#### Scenario: Restore reveal state
- **WHEN** the learner revisits or resumes a per-item submitted problem
- **THEN** recorded results and reference material remain expanded and the answer locked
- **AND** whole-Paper unsubmitted items still hide results except reference material explicitly disclosed through `不会`
