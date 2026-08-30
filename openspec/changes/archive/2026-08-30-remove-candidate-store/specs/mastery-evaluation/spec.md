## MODIFIED Requirements

### Requirement: Conservative knowledge-point propagation

A decisive failure from any linked formal problem SHALL support `needs_work` for every linked knowledge point. A knowledge point SHALL require qualifying positive evidence from two distinct linked problems across dates for `recently_stable`. If it has only one linked problem, stability SHALL additionally require a direct knowledge-point review on a different date; if it has no linked problem, it SHALL remain `evidence_insufficient`. The candidate store is physically removed: no candidate table, no candidate commands, and no candidate evidence path exist, so evaluations consider only formal problems, knowledge-point reviews, cards, and micro quizzes.

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

- **WHEN** any knowledge-point evaluation runs after the candidate store removal
- **THEN** no candidate evidence exists to consider: the evaluation cites only formal problems and direct knowledge-point reviews, and no formal-problem result is emitted for anything but formal problems
