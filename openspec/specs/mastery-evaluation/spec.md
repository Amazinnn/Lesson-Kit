# mastery-evaluation Specification

## Purpose
Provides a read-only and replaceable first experiment for classifying current learning evidence without presenting uncertain probabilities or changing the durable study model.
## Requirements
### Requirement: Read-only mastery experiment command

The workbench SHALL expose `wb experiment <workspace> mastery` for all entities or one knowledge point/problem, with optional JSON output. It SHALL return `evidence_insufficient`, `needs_work`, `due_review`, or `recently_stable`, a Chinese explanation, and traceable evidence reasons. It SHALL NOT output a mastery probability, change ordering, write a database row, or integrate with the student UI.

#### Scenario: Evaluate without writes

- **WHEN** the mastery command evaluates a workspace
- **THEN** the result contains categories and evidence reasons while database contents and row counts remain identical

#### Scenario: Request one formal problem

- **WHEN** the caller selects `--entity problem --id <id> --json`
- **THEN** one formal-problem evaluation is returned as JSON and candidate problems are absent

### Requirement: Versioned v0 problem evidence rules

The `v0` evaluator SHALL treat automatic correct/wrong/stuck results as strong evidence, ratings 1-2 as medium negative evidence, ratings 4-5 as medium positive evidence, and rating 3, notes, and skips as neutral. The latest decisive negative SHALL yield `needs_work`; absent current negative evidence, a due item SHALL yield `due_review`. `recently_stable` SHALL require positive evidence on at least two dates and at least one strong positive, or at least three positive self-ratings across at least two dates.

#### Scenario: Latest negative wins

- **WHEN** an item has earlier positive evidence and a later decisive wrong, stuck, or 1-2 rating
- **THEN** its category is `needs_work` with the later evidence identified

#### Scenario: Due follows negative precedence

- **WHEN** an item has no current decisive negative evidence and its schedule is due
- **THEN** its category is `due_review`

#### Scenario: Cross-date evidence establishes stability

- **WHEN** a problem has qualifying positive evidence across two dates including an automatic correct result
- **THEN** it may be `recently_stable`

#### Scenario: Neutral evidence does not change classification

- **WHEN** a learner only skips, writes notes, or submits rating 3
- **THEN** those events do not create positive or negative mastery evidence

### Requirement: Conservative knowledge-point propagation

A decisive failure from any linked formal problem SHALL support `needs_work` for every linked knowledge point. A knowledge point SHALL require qualifying positive evidence from two distinct linked problems across dates for `recently_stable`. If it has only one linked problem, stability SHALL additionally require a direct knowledge-point review on a different date; if it has no linked problem, it SHALL remain `evidence_insufficient`. Candidate rows are retired: candidate attempts SHALL NOT contribute evidence to any evaluation.

#### Scenario: Failure propagates to all owners

- **WHEN** a formal problem with multiple knowledge-point owners has decisive negative evidence
- **THEN** every owner evaluation cites that problem and may be `needs_work`

#### Scenario: Two problems support stability

- **WHEN** two different linked formal problems provide qualifying positive evidence across dates
- **THEN** the knowledge point may be `recently_stable`

#### Scenario: One-problem knowledge point needs direct review

- **WHEN** a knowledge point has one linked problem with qualifying positive evidence but no different-date direct knowledge-point review
- **THEN** it is not `recently_stable`

#### Scenario: Candidate evidence stays knowledge-point-only

- **WHEN** a gate-passed candidate attempt exists for a linked knowledge point
- **THEN** it contributes no evidence at all (candidate rows are retired): it cannot affect knowledge-point evaluation and no formal-problem result is emitted for the candidate

