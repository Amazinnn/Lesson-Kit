## MODIFIED Requirements

### Requirement: Rating invalidation on content change

Changing a problem's text, solution, knowledge-point membership, or problem
type SHALL clear its complete objective rating unless the same explicit JSON
mirror revision supplies a complete replacement vector. A replacement vector
SHALL be validated as a complete rating, and its total and model SHALL be
derived from the validated dimensions rather than trusted from the repository.
A content-only update SHALL clear the existing rating, leave the problem usable,
and SHALL NOT automatically rerate it. Partial vectors and direct edits to the
derived total or model SHALL remain invalid.

#### Scenario: Edit a rated problem

- **WHEN** an explicit content update changes the problem text
- **THEN** all difficulty fields become null and the problem remains in the pool

#### Scenario: Mirror content edit supplies an explicit replacement rating

- **GIVEN** a tracked problem has a complete difficulty group
- **AND** one JSON mirror revision changes its problem text and all four difficulty dimensions
- **WHEN** that revision is checked and synchronized
- **THEN** the complete vector is validated, its total and model are recomputed, and the replacement rating is stored
- **AND** a content edit without that complete vector still clears the existing rating
