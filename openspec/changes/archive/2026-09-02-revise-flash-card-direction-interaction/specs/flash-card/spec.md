## REMOVED Requirements

### Requirement: Flash card direction capability

**Reason**: mixed 偏好随会话级方向模型一并退役；能力要求整体替换为 forward/reverse
会话语义（见下方 ADDED）。

## ADDED Requirements

### Requirement: Flash card session direction

Card direction capability SHALL be content metadata, independent from the
direction selected for a practice session. A forward-only card SHALL produce
only a forward practice action. A bidirectional card SHALL produce distinct
forward and reverse actions without duplicating the content row. Each action
SHALL be ordered by its own `(card, direction)` schedule row; practicing or
excluding one direction SHALL NOT advance or exclude the other. The session
direction SHALL be chosen once when the session starts and SHALL be exactly
`forward` or `reverse`; it SHALL NOT change during the session. A forward
session SHALL produce forward actions. A reverse session SHALL produce the
reverse actions of bidirectional cards and SHALL retain forward-only cards
as forward actions. Pulls SHALL reject any other direction preference.
Existing pull callers that omit a preference or direction exclusions SHALL
retain the old forward-only behavior.

#### Scenario: Reverse session plays a bidirectional card's back

- **WHEN** a reverse pull reaches one card whose directions are `["forward", "reverse"]`
- **THEN** that card yields exactly its reverse action with independent due ordering

#### Scenario: Reverse preference keeps a forward-only card

- **WHEN** a reverse pull reaches a card whose directions are `["forward"]`
- **THEN** that card remains available as a forward action

#### Scenario: Exclude one practiced direction

- **WHEN** a pull excludes one `(card_id, direction)` key
- **THEN** only that action is removed and another allowed direction of the same card remains eligible

#### Scenario: Legacy pull stays forward-only

- **WHEN** a pull omits the direction preference and direction exclusions
- **THEN** it returns at most one forward action per card as before

#### Scenario: Unknown direction preference is rejected

- **WHEN** a pull sends a direction preference other than `forward` or `reverse`
- **THEN** the request is rejected with a visible 400 error and no cards are pulled
