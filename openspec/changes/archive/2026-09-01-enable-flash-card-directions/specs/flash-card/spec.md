## MODIFIED Requirements

### Requirement: Flash card content contract

The pool SHALL store flash cards in a dedicated additive `flash_cards` table
with five content fields: `card_id`, `kp_id`, `front`, `back`, and
`source_evidence`, plus one optional label field `topic_label` and one
direction-capability field `directions`. Each card SHALL reference exactly one
existing knowledge point, carry non-empty front and back text (front at most
100 characters, back at most 300 characters), and carry non-empty source
evidence. A supplied `topic_label` SHALL be a non-empty string of at most 40
characters that passes the shared markup safety check; an omitted label is
stored as null. `directions` SHALL be exactly `["forward"]` or
`["forward", "reverse"]`; an omitted value SHALL be stored as
`["forward"]` for compatibility. The knowledge point SHALL remain the single
source of truth; cards are derived key-value recall views over it, one atomic
fact per card, and no learning semantics SHALL be inferred from card text.

#### Scenario: A well-formed card enters the pool

- **WHEN** a manifest item satisfies the field contract and references an existing knowledge point
- **THEN** it is stored as one flash-card row preserving every supplied field and its normalized direction capability

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, exceeds a text bound, has an empty front or back, references a knowledge point that does not exist, or supplies an unsupported directions value
- **THEN** the deterministic gate rejects that item and nothing is written

#### Scenario: Label field validation

- **WHEN** a manifest item supplies a `topic_label` that is empty after trimming, exceeds 40 characters, or fails the markup safety check
- **THEN** the deterministic gate rejects that item with an explicit reason; an omitted `topic_label` is accepted and stored as null

#### Scenario: Legacy manifest defaults forward

- **WHEN** a valid flash-card item omits `directions`
- **THEN** the card is stored with `["forward"]` without a migration requirement for the manifest

## ADDED Requirements

### Requirement: Flash card direction capability

Card direction capability SHALL be content metadata, independent from the
direction selected for a practice session. A forward-only card SHALL produce
only a forward practice action. A bidirectional card SHALL produce distinct
forward and reverse actions without duplicating the content row. Each action
SHALL be ordered by its own `(card, direction)` schedule row; practicing or
excluding one direction SHALL NOT advance or exclude the other. A reverse
preference SHALL retain forward-only cards as forward actions. A mixed
preference SHALL expose both actions of bidirectional cards and the forward
action of forward-only cards. Existing pull callers that omit a preference or
direction exclusions SHALL retain the old forward-only behavior.

#### Scenario: Bidirectional card yields two mixed candidates

- **WHEN** a mixed pull reaches one card whose directions are `["forward", "reverse"]`
- **THEN** forward and reverse are separate candidates with independent due ordering

#### Scenario: Reverse preference keeps a forward-only card

- **WHEN** a reverse pull reaches a card whose directions are `["forward"]`
- **THEN** that card remains available as a forward action

#### Scenario: Exclude one practiced direction

- **WHEN** a pull excludes one `(card_id, direction)` key
- **THEN** only that action is removed and another allowed direction of the same card remains eligible

#### Scenario: Legacy pull stays forward-only

- **WHEN** a pull omits the direction preference and direction exclusions
- **THEN** it returns at most one forward action per card as before
