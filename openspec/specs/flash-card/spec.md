# flash-card Specification

## Purpose

Define flash cards as derived key-value recall views over knowledge points:
the knowledge point stays the single source of truth (one card holds one
atomic fact), a five-field additive table stores the cards, a
deterministic-gate ingest recipe brings them into the pool, and Flash Card is
the fourth practice mode — front, recall, reveal back, 1-5 self-rating with
no objective grading — backed by one independent scheduling row per card.
Leech handling, cloze-style automatic card derivation, and reverse-direction
cards remain future work.

## Requirements

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

### Requirement: Composable flash-card ingestion

Flash cards SHALL enter the pool only through a composable ingest recipe: a
manifest artifact of kind `flash-card-patch`, a deterministic contract gate,
a recoverable backup, and one explicit transactional apply. Card ids SHALL
follow `^[a-z0-9-]+-fc-\d{3}$` and SHALL be unique, including against ids
already in the pool. A failed apply SHALL leave the pool unchanged. Every
apply SHALL record one readable sequential batch id and stamp every inserted
card row with it, enabling whole-batch rollback as defined by the content
governance capability.

#### Scenario: Apply a valid card manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all cards are inserted in one committed transaction after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** any statement inside the apply transaction fails
- **THEN** the whole apply rolls back and the pool keeps its prior content

#### Scenario: Applied cards carry the batch id

- **WHEN** a gate-passed card manifest is applied
- **THEN** every inserted card row carries the recorded batch id

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
