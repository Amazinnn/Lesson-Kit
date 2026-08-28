## MODIFIED Requirements

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted, it SHALL fall back to `gate_passed`
candidates, and when both are exhausted it SHALL report the shortage per
knowledge point instead of inventing content. The pull request MAY carry
optional `include_ids`; when present, returned problems SHALL be restricted to
those identifiers within the requested scope, and combining `include_ids`
with an unscoped `all` mode SHALL be rejected.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** problems linked to that knowledge point are returned in
  weakness order

#### Scenario: Include filter restricts a scoped pull

- **WHEN** a scoped pull carries `include_ids` with one durable problem id
- **THEN** only that problem is returned, and the shortage report still
  reflects the remaining unfilled demand

#### Scenario: Include filter with unscoped all mode

- **WHEN** a pull carries `include_ids` together with `mode: all`
- **THEN** the request is rejected with 400 and nothing is pulled

## ADDED Requirements

### Requirement: Review page with card sessions

The workbench SHALL provide a fourth navigation page `复习` (review) rendered
in the three-column shell: a due-items overview grouped by due date with type
and direction badges, a scope handoff to practice, and an inline directional
card session as specified by the review-workbench capability. The page SHALL
follow the shared visual tokens and SHALL keep the card session's primary
action visible in the first screen.

#### Scenario: Open the review page

- **WHEN** the learner clicks the review navigation entry
- **THEN** the middle area shows the due-items overview for the current
  workspace and the review navigation entry is marked active

#### Scenario: Card session entry visibility

- **WHEN** no due row carries a direction
- **THEN** the card-session primary action is not shown and the page states
  the empty state honestly
