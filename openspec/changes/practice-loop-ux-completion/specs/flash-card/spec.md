## MODIFIED Requirements

### Requirement: Flash card practice mode

The practice page SHALL offer Flash Card as a fourth content mode alongside
exam, micro, and yes/no. A flash-card session SHALL scope to the explicit
knowledge-point selection, present one card front at a time, require an
explicit reveal before the back is shown, and collect a 1–5 self-rating
after the reveal. Flash cards SHALL have no options, no objective grading,
and no answer matching; both rating modes (immediate and batch) SHALL be
available. Each saved rating SHALL write one learning record with
`item_type='card'`, and each card SHALL hold exactly one independent
scheduling row (the per-direction key stays empty in this phase). A
flash-card session SHALL let the learner navigate back and forth within the
cards already presented in this session: revisiting a card SHALL preserve
its reveal state and collected state, an immediate-mode rated card SHALL be
read-only when revisited, and a skipped unrevealed card MAY be revealed on
revisit and then counts as played. New cards SHALL be pulled only when the
learner advances past the end of the presented history; pulls SHALL NOT
repeat cards already presented in the session. The session-end view SHALL
list played cards with front and back for unified rating. Pulls SHALL
return only cards inside the selected scope, due rows first, and SHALL
report an empty scope honestly instead of substituting other content.

#### Scenario: Play one card

- **WHEN** the learner reveals a card back and saves a rating
- **THEN** the feedback is recorded once for that card and the next card in
  scope is shown without repeats

#### Scenario: Revisit a revealed card

- **WHEN** the learner pages back to an earlier card of the same session
- **THEN** its front and already revealed back are shown with their state
  intact, and paging forward again replays the presented history without
  pulling a new card until the history end is passed

#### Scenario: Reveal a skipped card on revisit

- **WHEN** the learner pages back to a card that was skipped unrevealed and
  reveals it
- **THEN** the card counts as played and stays due for its session-end
  rating instead of remaining skipped

#### Scenario: Batch rating at session end

- **WHEN** a unified-rating flash-card session ends
- **THEN** the session-end view lists each played card with its front and
  back and collects the pending ratings there

#### Scenario: No cards in scope

- **WHEN** the selected scope holds no flash cards
- **THEN** the entry reports the shortage honestly and stays empty
