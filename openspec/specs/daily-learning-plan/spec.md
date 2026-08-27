# daily-learning-plan Specification

## Purpose
TBD - created by archiving change daily-learning-plan. Update Purpose after archive.
## Requirements
### Requirement: Baseline daily queue
The system SHALL produce a deterministic coarse-grained daily queue from active course goals, stage goals, progress, deadlines, coverage, and available formal problem types without requiring an Agent.

#### Scenario: Agent unavailable
- **WHEN** the Agent is unavailable or does not modify the plan
- **THEN** the baseline queue remains available and usable.

### Requirement: Goal and queue presentation
The practice page SHALL show long-term goals, stage goals, and today's queue together, with readable knowledge-point names and no micro-action checklist.

#### Scenario: Queue contains overlapping goals
- **WHEN** multiple goals affect the same day
- **THEN** the goals remain independently visible while today's queue presents a coarse aggregate action.

### Requirement: Student-selected practice path
The system SHALL let the student choose the existing exam, Flash Card, or Yes/No practice path for a queue item.

#### Scenario: Student chooses a path
- **WHEN** the student selects one of the three paths
- **THEN** the existing practice entry receives the selected scope without changing learning-write semantics.

### Requirement: Agent adjustment
The system SHALL allow an Agent to adjust the current workspace plan after explicit feedback or recalculation, and SHALL refresh affected plan views after a completed atomic batch.

#### Scenario: Adjustment fails
- **WHEN** Agent execution fails
- **THEN** the last valid plan or deterministic baseline remains visible and the current status truthfully reports failure.

### Requirement: Daily trigger and status
The system SHALL trigger at most one automatic recalculation on the first workspace opening of a local calendar day, SHALL allow explicit recalculation, and SHALL show a friendly live status while work runs.

#### Scenario: Application closed
- **WHEN** the application is not open
- **THEN** no heartbeat process runs and no plan is changed.

