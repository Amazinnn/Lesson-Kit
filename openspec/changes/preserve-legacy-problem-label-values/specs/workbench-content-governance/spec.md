## ADDED Requirements

### Requirement: Preserve retired problem-label history during ordinary schema ensure

An ordinary workbench schema ensure SHALL preserve an existing
`problems.topic_label` column and its values, including when it rebuilds a
compatible legacy problem table. Retiring the field from new problem inputs,
search and presentation SHALL NOT silently delete historical course data.
The retained column SHALL NOT become a new writing interface or search field.
Flash-card `topic_label` remains governed by its existing contract.

Destructive removal SHALL remain outside ordinary ensure until a separate
explicit removal migration is specified and approved. This change SHALL NOT
execute such a migration on existing course pools.

#### Scenario: Open a pool with historical problem labels

- **WHEN** ordinary schema ensure runs on a pool with populated problem labels
- **THEN** the labels, problem IDs and existing learning rows remain unchanged
- **AND** the retired field is still excluded from new problem inputs and UI

#### Scenario: Rebuild a compatible legacy problem table

- **WHEN** schema ensure upgrades a legacy problem table carrying labels
- **THEN** it copies the existing label values to the compatible table without loss

#### Scenario: Repeat schema ensure

- **WHEN** schema ensure runs again on the upgraded pool
- **THEN** the historical values are unchanged and no label-removal operation occurs
