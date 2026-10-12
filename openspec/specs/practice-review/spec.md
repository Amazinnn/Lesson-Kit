# practice-review Specification

## Purpose

Let a learner briefly inspect the immediately previous settled problem after practice has advanced, without reopening that problem for mutation or moving durable practice progress backward.

## Requirements

### Requirement: Review the immediately previous settled problem

When an ordinary problem has been settled and practice has advanced to the next unanswered ordinary problem, the practice page SHALL offer `回看上一题`. Activating it SHALL render the previous problem as a read-only result view containing the learner's submitted answer or `不会` state, any available verdict, and the available answer or solution. Submission, skip, reveal, and rating controls SHALL NOT mutate the reviewed problem.

#### Scenario: Review after advancing

- **WHEN** the learner has advanced from a settled ordinary problem to the next unanswered ordinary problem
- **THEN** `回看上一题` is available
- **AND** activating it shows the previous problem's settled result directly

#### Scenario: Return to the current problem

- **WHEN** the learner activates `返回当前题` from the previous-result view
- **THEN** the current unanswered problem is shown again
- **AND** any unsent text answer or selected choices from that current problem are restored

### Requirement: Review is an overlay, not practice navigation

Reviewing the previous problem SHALL NOT move the practice cursor, alter durable practice progress, create an attempt, write feedback, or reopen the previous problem for answering. Flash-card previous/next navigation SHALL retain its existing cursor-based behavior.

#### Scenario: Review leaves progress unchanged

- **WHEN** the learner opens and closes the previous-result view
- **THEN** the durable practice cursor and all attempt, feedback, and completion state remain unchanged

### Requirement: Agent context follows the visible reviewed problem

While the previous-result view is open, a new Agent turn from the practice page SHALL identify the reviewed problem as the focused problem and SHALL expose its settled answer as the focused answer. Returning to the current problem SHALL restore ordinary current-problem context.

#### Scenario: Ask the Agent while reviewing

- **WHEN** the learner sends an Agent message while the previous-result view is visible
- **THEN** the reviewed problem and its settled answer are the focused practice context without moving practice progress
