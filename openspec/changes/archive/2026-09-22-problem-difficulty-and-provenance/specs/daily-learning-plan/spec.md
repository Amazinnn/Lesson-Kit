## MODIFIED Requirements

### Requirement: Baseline daily queue

The system SHALL produce a deterministic coarse queue from goals, progress,
deadlines, coverage, available problem types, and available objective-
difficulty bands without requiring an Agent. Personal signals continue to
choose knowledge priority; objective difficulty contributes distribution and
suggested mix only. Unrated content remains available.

#### Scenario: Agent unavailable

- **WHEN** the Agent is unavailable or does not modify the plan
- **THEN** the baseline includes stable hidden difficulty distribution/mix data and remains usable

#### Scenario: Student presentation stays quiet

- **WHEN** a plan carries difficulty distribution data
- **THEN** the practice page does not display raw totals, dimensions, or stars
