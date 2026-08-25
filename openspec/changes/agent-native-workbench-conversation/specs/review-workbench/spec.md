## ADDED Requirements

### Requirement: Unified Agent data CLI

The workbench SHALL expose JSON data commands for get, list, search, history, create, update, delete, current-state replacement, candidate gating, and candidate promotion across knowledge points, formal problems, candidate problems, and knowledge relations. Read operations SHALL perform zero writes. A formal problem SHALL be created only by promoting a candidate that has passed both existing gates.

#### Scenario: Search without a write

- **WHEN** an Agent searches the pool through `wb data`
- **THEN** matching structured entities are returned and no content, learning, sequence, or conversation row changes

#### Scenario: Edit a candidate

- **WHEN** candidate content is explicitly updated
- **THEN** the candidate is updated and both gate states reset to pending

#### Scenario: Promote a gated candidate

- **WHEN** a candidate has passed structure and audit gates and the Agent explicitly promotes it
- **THEN** one formal problem with a readable sequence id is created and the candidate reflects promotion

### Requirement: Readable content sequences

New knowledge points, formal problems, candidates, and relations SHALL receive course/chapter-scoped sequential readable identifiers allocated atomically from an additive sequence table. Existing numeric identifiers SHALL seed the next value. No hash-derived identifier SHALL be used.

#### Scenario: Allocate after existing content

- **WHEN** the chapter already contains numbered entities and a new entity is explicitly created
- **THEN** its id uses the next readable number in that entity scope without scanning to reuse a deleted id
