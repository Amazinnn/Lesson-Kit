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

Answer Reveal Timing SHALL be selected before a new run and remain fixed for it. Submission Granularity SHALL be independent and changeable through the live settings. Explicit per-part submission SHALL lock that part after durable confirmation; whole-problem submission SHALL submit only its remaining unsubmitted parts. Whole-problem submission SHALL NOT complete the Paper. Inputs not yet submitted SHALL remain editable and recoverable. Single-choice and yes/no items in legacy per-item reveal mode SHALL retain selection-based submission when part submission is enabled; subjective and multiple-choice parts SHALL require an explicit submit action. Whole-problem granularity SHALL stage choices until explicit submission. Unconfirmed writes SHALL be labelled truthfully and remain recoverable.

In per-item reveal mode, confirmed submissions SHALL expand available reference material and eligible grading results, with pending or failed grading stated honestly. In whole-Paper reveal mode, part or whole-problem submission SHALL be allowed without prematurely disclosing final-answer conclusions, process conclusions, Extracted Answers, reference answers, solutions or evaluative explanations. Such content SHALL remain hidden until explicit final Paper submission, including in navigation previews, summaries and error filters. The interface SHALL be able to state that grading is complete but awaiting disclosure without revealing its outcome.

Explicit `不会` SHALL retain typed work and reveal available reference material for that part; it SHALL not silently disclose sibling-part references. Per-item reveal mode SHALL lock the stuck part. Whole-Paper reveal mode SHALL retain the existing revisable stuck draft until submission; entering a new answer MAY clear that draft mark while preserving that reference material was viewed. A committed stuck mark SHALL remain recorded when the Agent grades existing work. Navigation SHALL not clear it. An already disclosed answer SHALL NOT be treated as unseen. Agent-derived reference material SHALL be permitted under the provenance and uncertainty rules of agent-part-grading; absent material SHALL be stated honestly while none is available, never invented from self-rating.

#### Scenario: Submit a single-choice item
- **WHEN** the learner selects an option with per-part submission and per-item reveal enabled
- **THEN** the answer is submitted and, after confirmation, results and reference material appear with the answer locked

#### Scenario: Submit multiple-choice or text
- **WHEN** input changes without activating submit
- **THEN** it remains editable and undisclosed
- **AND** explicit submission locks it only after confirmation and follows the independent reveal policy

#### Scenario: Mark stuck in each mode
- **WHEN** the learner activates `不会`
- **THEN** available part-specific reference material is shown and typed work is preserved
- **AND** per-item reveal mode locks the part while whole-Paper mode allows a new answer to clear an uncommitted stuck draft before submission

#### Scenario: Reference material is unavailable
- **WHEN** an item has no recorded answer, solution or usable key and no Agent-derived reference is available
- **THEN** missing material and unavailable conclusions are stated honestly rather than inferred from self-rating

#### Scenario: Restore reveal state
- **WHEN** the learner revisits or resumes a submitted part
- **THEN** its answer remains locked and results obey the saved reveal policy, with previously viewed reference material still treated as viewed

#### Scenario: Submit early without seeing a result
- **WHEN** a learner explicitly submits a calculation part in whole-Paper reveal mode and the Agent completes grading
- **THEN** the part is saved and locked but its grading conclusions and answer comparison remain hidden until final Paper submission

#### Scenario: Final submission while grading is pending
- **WHEN** the learner explicitly submits the Paper while an accepted response is still being graded
- **THEN** the Paper can complete and reopen with truthful pending grading; later grading appears in that same archived answer sheet without reopening or resubmitting the run

### Requirement: Subjective error review uses disclosed independent conclusions

Practice review SHALL support locating subjective parts with wrong or partially correct conclusions in either applicable dimension, display which dimension matched, and retain problem, part and submission identity. Needs confirmation, unprovided answers, stuck marks and processing failures SHALL NOT be silently classified as wrong. Updated or withdrawn grading SHALL update the current filter outcome without rewriting prior attempts or learning projections. Whole-Paper undisclosed results SHALL NOT affect visible error counts or filters before disclosure.

#### Scenario: Review a calculation with wrong reasoning
- **WHEN** a disclosed calculation has a correct final result and a wrong process
- **THEN** error review includes that part with process wrong and answer correct, without assigning a total problem verdict

#### Scenario: Regrade a partial proof
- **WHEN** an Agent revises a disclosed proof from partially correct to correct
- **THEN** current partial-result filtering stops including it while the original response and revision history remain available
