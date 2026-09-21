## ADDED Requirements

### Requirement: Optional difficulty declaration

The workbench SHALL define difficulty as an optional attribute of pool problem
content. Every problem row SHALL be able to carry one difficulty value on a
1-5 scale, and every structured ingest path that carries difficulty SHALL
enforce only its form: a declared difficulty SHALL be an integer from 1 to 5
and SHALL be accompanied by a non-empty basis statement for the same item. A
declared difficulty without a basis SHALL fail the whole batch, while an
undeclared difficulty SHALL pass. The basis statement SHALL be gate-time
evidence only and SHALL NOT be stored in the pool. Knowledge-point declarations
and problem declarations SHALL share this optional semantics; the legacy
extraction pipeline's own defaulting behavior is outside this requirement.

#### Scenario: Declared difficulty passes

- **WHEN** a batch declares a difficulty value from 1 to 5 with a non-empty basis for an item
- **THEN** the gate accepts the batch and the applied row carries that difficulty

#### Scenario: Declared without a basis is rejected

- **WHEN** a batch declares a difficulty value for an item but supplies no basis statement
- **THEN** the gate rejects the whole batch and names the item

#### Scenario: Undeclared difficulty passes

- **WHEN** a batch declares no difficulty for any of its items
- **THEN** the gate accepts the batch and the applied rows keep a null difficulty

#### Scenario: Out-of-range difficulty is rejected

- **WHEN** a batch declares a difficulty outside 1-5, or a non-integer value
- **THEN** the gate rejects the whole batch and names the item

#### Scenario: Basis is not persisted

- **WHEN** a batch with declared difficulty and basis statements is applied
- **THEN** the pool stores the difficulty values and stores no basis text

#### Scenario: Knowledge points share the optional semantics

- **WHEN** a knowledge-point patch omits difficulty entirely
- **THEN** the gate accepts it, while a patch that declares a difficulty without a basis is rejected
