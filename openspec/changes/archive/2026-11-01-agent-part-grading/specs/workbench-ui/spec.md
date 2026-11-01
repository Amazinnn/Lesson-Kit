## ADDED Requirements

### Requirement: Live submission granularity in existing settings

The existing workspace settings view SHALL allow choosing per-part submission, with a whole-problem action for the remaining parts, or whole-problem submission only. The default SHALL enable per-part submission and the whole-problem action. Changes SHALL update the active ordinary practice view immediately, persist using existing workspace browser preferences and synchronize across its tabs. Switching SHALL preserve drafts, committed responses, grading, cursor, scroll position and reference-viewing facts; it SHALL NOT submit, unlock, regrade, complete a run or change Answer Reveal Timing. Existing submitted parts SHALL remain locked and other settings SHALL retain their own contracts.

#### Scenario: Change granularity during practice
- **WHEN** a learner changes to whole-problem submission while one part is submitted and another has a draft
- **THEN** controls update without restarting, the submitted part stays locked, the draft is retained, and submitting the whole problem later submits only remaining parts

### Requirement: Subjective and mixed-problem answering status

The practice Answering Status area and numbered navigation SHALL expose meaningful subjective states, separating response state, grading progress, stuck marks and disclosed final-answer/process conclusions. A subjective problem without parts SHALL receive the same state presentation as a subjective part. Mixed parents SHALL show completion progress and counts of applicable states, with expandable part details, rather than a single parent correct/wrong/partial verdict. Counts SHALL identify their dimension so correct final answers and wrong processes are not mistaken for disjoint part totals. Blank answers, failures and uncertainty SHALL not appear as wrong. Hidden outcomes SHALL be masked consistently across labels, colors, badges, counts and accessible descriptions.

#### Scenario: Mixed progress in one problem
- **WHEN** a four-part problem has a correct objective part, a calculation being graded, a proof marked stuck and an unanswered part
- **THEN** its summary presents the progress and applicable state counts, and details identify each part without asserting a total verdict

#### Scenario: Preserve separate subjective conclusions
- **WHEN** a disclosed calculation has answer correct and process wrong
- **THEN** both labelled conclusions appear in its status details and no synthesized single subjective verdict replaces them

#### Scenario: Do not leak hidden grading
- **WHEN** whole-Paper reveal mode has a completed but undisclosed wrong result
- **THEN** the number button, status area, preview and accessible descriptions show only permitted workflow information, without a wrong color, count or label

### Requirement: Number-button previews and scrollable mixed answering

Hovering a problem-number button SHALL temporarily show its part statuses in saved order; keyboard focus SHALL provide the same information. Leaving both the button and preview SHALL dismiss the transient preview, and Escape SHALL close it. The pointer SHALL be able to move into the preview to read or scroll it. Click or touch SHALL offer equivalent persistent details without requiring hover. Previewing SHALL NOT navigate, submit, reveal hidden outcomes or modify records. Long previews and long mixed problems SHALL support wheel scrolling with reachable prompts, inputs and results. Each part's answering controls SHALL be adjacent to its prompt; updates SHALL preserve drafts and reading position.

#### Scenario: Inspect without navigating
- **WHEN** the learner hovers or focuses a number for a mixed problem while editing another problem
- **THEN** a temporary preview shows that problem's permitted part statuses without changing the current question or draft

#### Scenario: Use a long problem and preview
- **WHEN** a mixed problem or its part-status preview exceeds the available height
- **THEN** the learner can scroll to every part and its controls, and keyboard or touch users can access equivalent status details
