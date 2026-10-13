## MODIFIED Requirements

### Requirement: Rating invalidation on content change

Changing a problem's text, solution, knowledge-point membership, or problem
type SHALL clear its complete objective rating unless the same explicit JSON
mirror revision supplies a complete replacement vector whose four dimensions
include at least one value different from the synchronized baseline. All four
dimensions SHALL be present and validated; unchanged dimension values MAY be
carried in the vector. Its total and model SHALL be derived from the validated
dimensions rather than trusted from the repository. A full vector carried
unchanged alongside a content-axis edit SHALL NOT count as a replacement and
the stale rating SHALL still be cleared. An all-null group SHALL continue to
clear the rating. A content-only update SHALL leave the problem usable and
SHALL NOT automatically rerate it. Partial vectors and direct edits to the
derived total or model SHALL remain invalid.

#### Scenario: Edit a rated problem

- **WHEN** an explicit content update changes the problem text
- **THEN** all difficulty fields become null and the problem remains in the pool

#### Scenario: Mirror content edit supplies a changed complete replacement vector

- **GIVEN** a tracked problem has a complete difficulty group
- **AND** one JSON mirror revision changes its problem text and supplies all four non-null dimensions with at least one value different from the synchronized baseline
- **WHEN** that revision is checked and synchronized
- **THEN** the complete vector is validated, its total and model are recomputed, and the replacement rating is stored
- **AND** unchanged dimension values in that complete vector are allowed

#### Scenario: A carried-over complete vector is cleared after a content edit

- **GIVEN** a tracked problem has a complete difficulty group in its synchronized baseline
- **AND** one JSON mirror revision changes its problem text but carries all four baseline dimension values unchanged
- **WHEN** that revision is checked and synchronized
- **THEN** the carried-over vector is not treated as a replacement rating, all existing difficulty fields become null, and the problem remains in the pool
