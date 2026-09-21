## MODIFIED Requirements

### Requirement: Read-only mastery experiment command

The workbench SHALL expose `lesson-kit experiment <workspace> mastery` for all entities or one knowledge point/problem, with optional JSON output. It SHALL return `evidence_insufficient`, `needs_work`, `due_review`, or `recently_stable`, a Chinese explanation, and traceable evidence reasons. It SHALL NOT output a mastery probability, change ordering, write a database row, or integrate with the student UI.

#### Scenario: Evaluate without writes

- **WHEN** the mastery command evaluates a workspace
- **THEN** the result contains categories and evidence reasons while database contents and row counts remain identical

#### Scenario: Request one formal problem

- **WHEN** the caller selects `--entity problem --id <id> --json`
- **THEN** one formal-problem evaluation is returned as JSON and candidate problems are absent
