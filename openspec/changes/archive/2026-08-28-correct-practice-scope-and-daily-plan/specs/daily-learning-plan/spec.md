## MODIFIED Requirements

### Requirement: Baseline daily queue
The system SHALL produce a deterministic coarse-grained daily queue from real
active goals, progress, deadlines, coverage, and available formal content.
The queue SHALL contain at most three holistic items and SHALL NOT invent a
course goal, duration, mastery value, or micro-action checklist. When no goals
exist, it SHALL report only due or available work.

#### Scenario: No goals exist
- **WHEN** the workspace has no persisted long-term or stage goals
- **THEN** the plan omits goal cards and reports due/available queue data without
  fabricating a default goal

#### Scenario: Agent unavailable
- **WHEN** the Agent is unavailable or does not modify the plan
- **THEN** the deterministic queue remains available and usable

#### Scenario: Queue is capped
- **WHEN** more than three candidate queue items could be produced
- **THEN** the deterministic plan returns no more than three coarse items

### Requirement: Goal and queue presentation
The practice page SHALL show independent cards for each real long-term and
stage goal plus a separate coarse daily queue. Goal cards SHALL default to
title, progress, and deadline; details are on demand.

#### Scenario: Overlapping real goals
- **WHEN** multiple real goals affect the same day
- **THEN** each goal remains independently visible while the daily queue presents
  a coarse aggregate action

#### Scenario: Queue contains overlapping goals
- **WHEN** multiple goals affect the same day
- **THEN** the goals remain independently visible while today's queue presents a
  coarse aggregate action

### Requirement: Queue handoff
Selecting a queue item SHALL seed the explicit knowledge-view selection and then
open the mode picker; it SHALL NOT pull a problem or bypass mode selection.

#### Scenario: Handoff from today's queue
- **WHEN** the learner activates a queue item with a knowledge scope
- **THEN** that scope becomes the current tab selection and practice waits for
  exactly one selected mode
