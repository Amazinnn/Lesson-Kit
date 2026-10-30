## ADDED Requirements

### Requirement: Source-preserving live long-text editing
Every editable long-text field SHALL use source-preserving live Markdown editing with the shared safe Markdown subset and LaTeX rendering. Selection-intersecting blocks SHALL show source and other complete blocks SHALL render in place. Unclosed syntax SHALL stay editable. Short fields SHALL remain unchanged.

#### Scenario: No-op editing
- **WHEN** a learner opens, focuses, blurs or saves unchanged Markdown
- **THEN** source remains character-for-character unchanged, including blank lines and delimiters

#### Scenario: Input and recovery
- **WHEN** a learner edits or restores an answer, note, goal description, Agent input, pending message or knowledge-point experience
- **THEN** existing draft, submission, selection and navigation behavior remains intact
- **AND** display-only changes do not emit content changes

### Requirement: Existing interaction and safety boundaries
The editor SHALL preserve existing submit and lock rules, safe link/image restrictions, plain Markdown storage and Chinese input composition.

#### Scenario: Agent keyboard
- **WHEN** Enter is pressed outside composition in Agent input
- **THEN** it sends, while Shift+Enter inserts a newline
- **AND** Enter during composition does not send

#### Scenario: Submitted answer
- **WHEN** an answer is already submitted, including Agent-imported answers
- **THEN** its answer remains locked and cannot be edited

#### Scenario: Local assets unavailable
- **WHEN** editor initialization fails
- **THEN** the original textarea remains usable with a visible warning
