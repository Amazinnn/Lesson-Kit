## ADDED Requirements

### Requirement: Workspace goals

The workbench SHALL provide additive list/create/update/delete operations for
real long-term and stage goals in the workspace-local goal store. Missing or
empty stores SHALL render an honest empty state.

#### Scenario: Create a goal
- **WHEN** a user explicitly submits a title and deadline
- **THEN** the goal is saved once and appears as a goal card after refresh

### Requirement: Plan refresh

An explicit recalculation SHALL persist one versioned plan and replace the full
visible goal and queue region. It SHALL not create learning records.

#### Scenario: Recalculate and refresh
- **WHEN** the learner explicitly requests a recalculation
- **THEN** the saved plan version changes and the complete visible goal and
  queue region is replaced with the returned plan

