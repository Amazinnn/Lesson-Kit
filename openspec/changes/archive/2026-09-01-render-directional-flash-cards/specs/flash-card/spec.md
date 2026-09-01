## MODIFIED Requirements

### Requirement: Flash card practice mode

The practice page SHALL offer Flash Card as a fourth content mode alongside
exam, micro, and yes/no. Selecting Flash Card SHALL expose a forward, reverse,
or mixed session preference, with mixed selected by default; forward-only cards
SHALL remain forward actions under every preference. A flash-card session SHALL
scope to the explicit knowledge-point selection, present one prompt at a time,
require an explicit reveal before the answer is shown, and collect a 1–5
self-rating after the reveal. A bidirectional card SHALL expose one compact
direction-swap action before and after reveal; swapping SHALL exchange the
current prompt and answer, and the saved rating SHALL carry the direction that
was actually used. Flash cards SHALL have no options, no objective grading,
and no answer matching; both rating modes (immediate and batch) SHALL be
available. Each saved rating SHALL write one learning record with
`item_type='card'` and advance only its concrete direction schedule row.

A forward-only card SHALL reveal its other side by expanding the card downward.
A bidirectional card SHALL appear as two stacked cards and reveal by fanning the
prompt toward the lower left and the answer toward the lower right, keeping both
sides readable without a 3D flip. Reduced-motion preferences SHALL show the same
final state without positional animation.

A flash-card session SHALL let the learner navigate back and forth within the
direction actions already presented in this session: revisiting an action SHALL
preserve its direction, reveal state, and collected state; an immediate-mode
rated action SHALL be read-only when revisited; and a skipped unrevealed action
MAY be revealed on revisit and then counts as played. New actions SHALL be pulled
only when the learner advances past the end of the presented history. In a mixed
session, forward and reverse actions of one bidirectional content card MAY both
appear and SHALL remain distinct history entries. The session-end view SHALL
list played card actions with the actual prompt, answer, and direction for
unified rating. Pulls SHALL return only cards inside the selected scope, due
direction rows first, and SHALL report an empty scope honestly instead of
substituting other content.

#### Scenario: Play one card

- **WHEN** the learner reveals a card answer and saves a rating
- **THEN** feedback is recorded once for the concrete card direction and the next action in scope is shown without repeating that direction action

#### Scenario: Choose a reverse session

- **WHEN** the learner selects reverse before starting Flash Card practice
- **THEN** bidirectional cards ask with back and answer with front while forward-only cards remain front-to-back

#### Scenario: Swap the current bidirectional card

- **WHEN** the learner activates ⇄ on a bidirectional card before or after reveal
- **THEN** its prompt and answer exchange, its view state remains intact, and a later rating targets the resulting direction

#### Scenario: Reveal one forward-only card

- **WHEN** the learner reveals a forward-only card
- **THEN** its other side expands downward and no direction-swap action is shown

#### Scenario: Reveal one bidirectional card

- **WHEN** the learner reveals a bidirectional card
- **THEN** the two stacked faces fan toward opposite lower corners and both remain readable

#### Scenario: Reduced motion reveal

- **WHEN** the learner prefers reduced motion and reveals either card type
- **THEN** the final revealed layout appears without a positional transition

#### Scenario: Revisit a revealed card

- **WHEN** the learner pages back to an earlier direction action of the same session
- **THEN** its actual prompt, answer, direction, and reveal state are shown intact, and paging forward replays history before pulling

#### Scenario: Reveal a skipped card on revisit

- **WHEN** the learner pages back to a card action that was skipped unrevealed and reveals it
- **THEN** the action counts as played and stays due for its session-end rating instead of remaining skipped

#### Scenario: Batch rating at session end

- **WHEN** a unified-rating flash-card session ends
- **THEN** each played action lists its actual prompt, answer, and direction and collects a rating for that direction

#### Scenario: No cards in scope

- **WHEN** the selected scope holds no flash cards
- **THEN** the entry reports the shortage honestly and stays empty
