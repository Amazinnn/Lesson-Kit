## ADDED Requirements

### Requirement: Complete primary learning text

The workbench SHALL display user-authored knowledge titles, questions, notes, goal
titles, and practice-scope titles in full. These primary labels SHALL wrap within
their available column and SHALL NOT use ellipsis. Flex and grid containers around
them SHALL allow content children to shrink without widening the three-column shell.

#### Scenario: Long unbroken title

- **WHEN** a primary title contains a string wider than its column
- **THEN** it wraps inside the column without clipping or widening the page

#### Scenario: Practice scope title

- **WHEN** a selected or suggested knowledge title spans several lines
- **THEN** every character remains visible and adjacent controls remain usable

### Requirement: Locally scroll wide artifacts

Code blocks, display mathematics, and tables SHALL remain complete and SHALL scroll
horizontally inside their own rendered surface when wider than the available column.
Long inline-code tokens SHALL wrap. None of these artifacts SHALL widen the middle
page or Agent column.

#### Scenario: Wide code block

- **WHEN** a code line is wider than the content column
- **THEN** the code surface scrolls horizontally while the page width stays fixed

#### Scenario: Wide table in Agent output

- **WHEN** an Agent message contains a table wider than the right column
- **THEN** the table scrolls locally and the conversation composer remains in view
