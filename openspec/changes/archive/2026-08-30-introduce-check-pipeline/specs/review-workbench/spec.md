## MODIFIED Requirements

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted it SHALL report the shortage per knowledge
point instead of inventing content or falling back to candidate staging.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered, with none repeated within the same session

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point and the UI points to the Check pipeline as the content path instead of fabricating problems

### Requirement: Unified Agent data CLI

The workbench SHALL expose JSON data commands for get, list, search, history,
create, update, delete, current-state replacement, candidate gating, and
candidate promotion across knowledge points, formal problems, candidate
problems, and knowledge relations. Read operations SHALL perform zero writes.
Within this data CLI a formal problem SHALL be created only by promoting a
candidate that has passed both existing gates. The candidate command family
SHALL be retired (待退役): it receives no new capabilities, and the Check
pipeline SHALL be the content path for adding formal problems.

#### Scenario: Search without a write

- **WHEN** an Agent searches the pool through `wb data`
- **THEN** matching structured entities are returned and no content, learning, sequence, or conversation row changes

#### Scenario: Edit a candidate

- **WHEN** candidate content is explicitly updated
- **THEN** the candidate is updated and both gate states reset to pending

#### Scenario: Promote a gated candidate

- **WHEN** a candidate has passed structure and audit gates and the Agent explicitly promotes it
- **THEN** one formal problem with a readable sequence id is created and the candidate reflects promotion
