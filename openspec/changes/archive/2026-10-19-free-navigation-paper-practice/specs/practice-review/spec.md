## REMOVED Requirements

### Requirement: Review is an overlay, not practice navigation
**Reason**: Ordinary Paper problems now use one freely navigable answering/review surface with recoverable position rather than an isolated overlay. Flash-card behavior is outside this replacement.
**Migration**: Use Free navigation throughout a Paper and Mode-specific answer reveal and locking. Merely navigating still creates no learning evidence. Existing historical submissions remain immutable.

### Requirement: Review completed ordinary problems throughout a Paper run
**Reason**: Navigation must include unanswered items and completed executions, with mode-specific reveal rather than collapse on every entry.
**Migration**: Use the new navigation and reveal requirements; preserve original records and truthful missing/unconfirmed states.

## MODIFIED Requirements

### Requirement: Agent context follows the visible reviewed problem

A new Agent turn from ordinary Paper practice SHALL use the visible problem and that run's answer or draft as focused context, whether answering, browsing a locked item, or viewing a completed answer sheet. Previously accepted messages SHALL retain submission-time context. Changing the visible item SHALL NOT submit an answer or create learning evidence.

#### Scenario: Ask the Agent while reviewing
- **WHEN** the learner sends an Agent message while a reviewed result is visible
- **THEN** that problem and submitted answer are focused context without another submission

#### Scenario: Navigate after sending
- **WHEN** the learner sends a message while viewing A and then views B
- **THEN** a new message uses B while the accepted message keeps A's context

## ADDED Requirements

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
