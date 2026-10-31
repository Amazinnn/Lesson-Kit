## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Subjective error review uses disclosed independent conclusions

Practice review SHALL support locating subjective parts with wrong or partially correct conclusions in either applicable dimension, display which dimension matched, and retain problem, part and submission identity. Needs confirmation, unprovided answers, stuck marks and processing failures SHALL NOT be silently classified as wrong. Updated or withdrawn grading SHALL update the current filter outcome without rewriting prior attempts or learning projections. Whole-Paper undisclosed results SHALL NOT affect visible error counts or filters before disclosure.

#### Scenario: Review a calculation with wrong reasoning
- **WHEN** a disclosed calculation has a correct final result and a wrong process
- **THEN** error review includes that part with process wrong and answer correct, without assigning a total problem verdict

#### Scenario: Regrade a partial proof
- **WHEN** an Agent revises a disclosed proof from partially correct to correct
- **THEN** current partial-result filtering stops including it while the original response and revision history remain available
