# Linked problem full reading

## MODIFIED Requirements

### Requirement: Knowledge point linked problems use complete readable statements
The knowledge point page SHALL group linked formal problems by topic label. Topic groups SHALL be collapsed by default. After a group is opened, each row SHALL show a concise display title followed directly by the complete stored problem statement rendered with the workbench safe Markdown subset. The linked-problem area SHALL NOT render `display_summary`, truncated excerpts, ellipsis characters, or raw problem ids.

`display_summary` MAY remain as compatible metadata for normalized statements longer than 500 characters. It is optional and SHALL NOT be required for display or validation of a long problem.

#### Scenario: Open a topic group

- **WHEN** a learner opens a topic group on a knowledge point page
- **THEN** the group reveals rows containing the short title and complete rendered statement, with no summary layer or nested full-statement disclosure

#### Scenario: Long statement has no summary

- **WHEN** a linked problem is longer than 500 normalized characters and has no valid display summary
- **THEN** the row still displays its complete statement without manufacturing a summary or truncating the text

#### Scenario: Missing display title

- **WHEN** a linked problem has no display title
- **THEN** the row uses the fixed readable fallback `未命名题目` and never exposes the raw problem id as primary text
