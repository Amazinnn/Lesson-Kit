## MODIFIED Requirements

### Requirement: Knowledge point display page

The knowledge point display page SHALL render linked problems grouped by their topic label. Each row SHALL present a concise problem title as primary text. Problems whose normalized statement exceeds 300 characters MAY present a persisted Chinese one-sentence summary of at most 48 characters as secondary text. Every row SHALL allow the learner to reveal the complete problem statement without runtime truncation. Raw problem ids and ellipsis-truncated statement excerpts SHALL NOT appear in linked-problem rows.

#### Scenario: Browse grouped linked problems

- **WHEN** a knowledge point has linked problems from multiple topics
- **THEN** the page displays separate labeled groups containing concise problem titles

#### Scenario: Read a long linked problem

- **WHEN** a linked problem exceeds 300 normalized characters and has a valid display summary
- **THEN** its row shows the complete stored summary and can reveal the full statement without an ellipsis

#### Scenario: Read a short linked problem

- **WHEN** a linked problem is at most 300 normalized characters
- **THEN** its row shows the title without manufacturing a secondary excerpt and can reveal the full statement

#### Scenario: Missing long-problem summary

- **WHEN** a long linked problem has no valid persisted summary
- **THEN** its row shows the title and full-statement disclosure without falling back to a truncated excerpt

#### Scenario: Navigate a wiki link

- **WHEN** the learner clicks a wiki link in a knowledge point body
- **THEN** the display page navigates to the linked knowledge point

#### Scenario: See signal reasons

- **WHEN** the knowledge point has signals or cascade boosts
- **THEN** the display page shows the signal weight and the cascade reason text
