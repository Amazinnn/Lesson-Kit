## ADDED Requirements

### Requirement: Explicit Paper answer import

When the learner explicitly asks to import answers written on paper, the Agent
MAY resolve the target saved Paper, run `lesson-kit attempts check|apply` with a
manifest carrying `paper_id`, and report the binding result and current Paper
progress. The Agent SHALL NOT modify the saved Paper JSON directly.

If the learner's answer names a problem that does not exist in the pool, the
Agent SHALL use the governed content path to create it, attach it to an existing
knowledge point with source evidence, append it to the Paper with `papers
append`, and only then import the attempt. The Agent SHALL NOT invent the
problem's content, knowledge point, or source evidence. The Agent SHALL NOT
import an answer when the learner has not asked to record it.

#### Scenario: Import answers into the selected Paper

- **WHEN** the learner asks the Agent to record photographed answers that belong to the selected saved Paper
- **THEN** the Agent checks and applies one manifest with that `paper_id`, and reports the bound items and updated progress

#### Scenario: Import answers into a paused Paper

- **WHEN** the learner names a different saved Paper that has unfinished progress
- **THEN** the Agent binds the attempts to that Paper's checkpoint without changing the selected Paper

#### Scenario: Repair a missing problem before importing

- **WHEN** a photographed answer belongs to a problem absent from the pool
- **THEN** the Agent creates the problem under an existing knowledge point, appends it to the Paper, and imports the attempt in that order

#### Scenario: Refuse an import without explicit intent

- **WHEN** the learner is only discussing the answer or asking for an explanation
- **THEN** the Agent reads context but creates no attempt, Paper progress, or evaluation
