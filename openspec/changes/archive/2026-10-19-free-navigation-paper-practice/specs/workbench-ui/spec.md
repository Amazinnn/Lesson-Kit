## REMOVED Requirements

### Requirement: Compact per-problem self-rating
**Reason**: Self-rating must not own navigation or require a record-and-next action.
**Migration**: Retain compact accessible numeric 1–5 input and optional note under Independent self-rating during Paper practice; preserve validation and feedback semantics.

### Requirement: Session-end unified self-rating
**Reason**: Paper completion must not depend on finishing self-rating; replay creates a new run rather than a learner assembly action.
**Migration**: Use Independent self-rating during Paper practice and Paper completion and answer-sheet return. Separately requested Agent/CLI follow-up assembly remains available.

## ADDED Requirements

### Requirement: Minimal Paper start and practice controls

The start surface SHALL show selected Paper title, item count, Answer Reveal Timing and start action. An unfinished run SHALL instead offer continuation with original timing, without restarting or changing timing. The old content-mode, rating-timing, quantity, save-from-selection and source-filter configuration block SHALL be absent. Ordinary navigation SHALL retain `上一题`, `下一题`, `不会`, plus `提交答案` only for multiple-choice and text in per-item mode. Paper-level `提交试卷` and `暂停练习` SHALL remain available; the obsolete session-only unsaved-content hint SHALL be removed. Locked-item mutation controls SHALL be disabled or absent without blocking navigation or self-rating edits.

#### Scenario: Start and resume
- **WHEN** a learner starts and later resumes a Paper
- **THEN** start selects timing and continuation restores it without the old setup block

#### Scenario: Navigate without submitting
- **WHEN** a learner navigates, pauses, or reaches the final item
- **THEN** the Paper is not submitted and pause is labelled `暂停练习`

### Requirement: Accessible Paper status dots

A compact numbered status-dot panel SHALL navigate to every item. Whole-Paper mode before submission SHALL distinguish unanswered, filled and stuck without showing correctness. Per-item mode SHALL show correct/wrong only with usable verdicts, and distinguish filled-but-unsubmitted from submitted-without-verdict. Current item SHALL have an outline or equivalent non-color cue. Statuses SHALL have readable accessible names, not color alone; many items SHALL not obscure the question or navigation.

#### Scenario: No premature grading cues
- **WHEN** answers are filled in whole-Paper mode before submission
- **THEN** colors, text, badges and summaries show filled status without exposing right/wrong

#### Scenario: Jump and read status
- **WHEN** any numbered dot is activated
- **THEN** the question appears with accessible status and a distinct current-item indicator

### Requirement: Independent self-rating during Paper practice

The run SHALL preserve its existing self-rating preference. When enabled, eligible items SHALL expose compact numeric 1–5 input and optional note after per-item submission or whole-Paper submission according to Answer Reveal Timing. Self-rating SHALL be optional, SHALL NOT gate navigation or completion, and SHALL remain editable through the existing same-run overwrite rule. Missing self-rating SHALL NOT mean correctness. Invalid or failed saves SHALL retain edits and report errors. When disabled, self-rating controls SHALL be absent and existing verdict-driven learning semantics SHALL remain unchanged. No record-and-next action SHALL be required.

#### Scenario: Rate a text answer
- **WHEN** a text answer is submitted in per-item mode with self-rating enabled
- **THEN** the learner may compare the reference and save a rating or continue without one

#### Scenario: Whole-Paper answers and optional ratings
- **WHEN** final submission contains eligible unrated items
- **THEN** completion succeeds and items remain available for later self-rating

#### Scenario: Edit or reject a rating
- **WHEN** a linked rating is edited
- **THEN** valid edits overwrite only that same-run rating/note without replaying learning effects
- **AND** empty or out-of-range saves are rejected without writes and the editor stays usable

#### Scenario: Self-rating disabled
- **WHEN** self-rating is disabled
- **THEN** answers/results work without rating inputs, note fields or feedback save actions

### Requirement: Paper completion and answer-sheet return

Successful explicit final submission SHALL show a congratulations-style surface with total items, objective correct/wrong, stuck and pending self-rating counts. Counts SHALL be truthful; overlapping stuck/wrong SHALL not be presented as disjoint totals, unavailable verdict SHALL not become wrong, and completion SHALL not claim all answers are correct. Actions SHALL include `查看本次答卷`, `再练一次`, `返回试卷列表`. Answer-sheet review SHALL permit arbitrary navigation with fixed recorded answers and editable eligible self-ratings, with an explicit return to the same run's completion surface without resubmission. Starting again SHALL create a distinct run and preserve the completed one.

#### Scenario: Review and return
- **WHEN** the learner views an answer sheet, changes item or self-rating, and returns to completion
- **THEN** the same run's completion and current rating counts appear without another Attempt or archive

#### Scenario: Practice again
- **WHEN** the learner starts again from completion
- **THEN** a new run starts from that Paper with a fresh start choice and the previous answer sheet remains intact
