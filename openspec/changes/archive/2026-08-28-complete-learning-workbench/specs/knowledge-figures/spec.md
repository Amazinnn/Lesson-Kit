## ADDED Requirements

### Requirement: Existing-metric projections

The graph MAY project existing `problem_count`, `importance`, `state`, or edge
`attraction` into visual emphasis. The structural relationship layout SHALL
remain the default, projections SHALL be deterministic, and coordinates SHALL
not be persisted.

#### Scenario: Switch projection
- **WHEN** the learner selects an existing-metric projection
- **THEN** the graph changes visual emphasis without changing its edges,
  selection, or persisted data
