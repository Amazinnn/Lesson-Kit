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
with exactly five fields: `card_id`, `kp_id`, `front`, `back`, and
`source_evidence`. Each card SHALL reference exactly one existing knowledge
point, carry non-empty front and back text (front at most 100 characters,
back at most 300 characters), and carry non-empty source evidence. The
knowledge point SHALL remain the single source of truth; cards are derived
key-value recall views over it, one atomic fact per card, and no learning
semantics SHALL be inferred from card content.

#### Scenario: A well-formed card enters the pool

- **WHEN** a manifest item satisfies the field contract and references an
  existing knowledge point
- **THEN** it is stored as one flash-card row preserving every supplied field

#### Scenario: Contract violation

- **WHEN** an item lacks source evidence, exceeds a text bound, has an empty
  front or back, or references a knowledge point that does not exist
- **THEN** the deterministic gate rejects that item and nothing is written

### Requirement: Composable flash-card ingestion

Flash cards SHALL enter the pool only through a composable ingest recipe: a
manifest artifact of kind `flash-card-patch`, a deterministic contract gate,
a recoverable backup, and one explicit transactional apply. Card ids SHALL
follow `^[a-z0-9-]+-fc-\d{3}$` and SHALL be unique, including against ids
already in the pool. A failed apply SHALL leave the pool unchanged.

#### Scenario: Apply a valid card manifest

- **WHEN** the recipe applies a gate-passed manifest
- **THEN** all cards are inserted in one committed transaction after a
  recoverable backup is written

#### Scenario: Apply fails midway

- **WHEN** any statement inside the apply transaction fails
- **THEN** the whole apply rolls back and the pool keeps its prior content

### Requirement: Flash card practice mode

The practice page SHALL offer Flash Card as a fourth content mode alongside
exam, micro, and yes/no. A flash-card session SHALL scope to the explicit
knowledge-point selection, present one card front at a time, require an
explicit reveal before the back is shown, and collect a 1–5 self-rating
after the reveal. Flash cards SHALL have no options, no objective grading,
and no answer matching; both rating modes (immediate and batch) SHALL be
available. Each saved rating SHALL write one learning record with
`item_type='card'`, and each card SHALL hold exactly one independent
scheduling row (the per-direction key stays empty in this phase). The
session-end view SHALL list played cards with front and back for unified
rating. Pulls SHALL return only cards inside the selected scope, due rows
first, and SHALL report an empty scope honestly instead of substituting
other content.

#### Scenario: Play one card

- **WHEN** the learner reveals a card back and saves a rating
- **THEN** the feedback is recorded once for that card and the next card in
  scope is shown without repeats

#### Scenario: Batch rating at session end

- **WHEN** a unified-rating flash-card session ends
- **THEN** the session-end view lists each played card with its front and
  back and collects the pending ratings there

#### Scenario: No cards in scope

- **WHEN** the selected scope holds no flash cards
- **THEN** the entry reports the shortage honestly and stays empty
