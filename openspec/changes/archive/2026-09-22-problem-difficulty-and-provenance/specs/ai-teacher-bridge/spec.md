## ADDED Requirements

### Requirement: Explicit Agent difficulty rating

An Agent MAY invoke difficulty check and apply only when the learner explicitly
asks to rate or rerate named problems. Ordinary conversation, content ingest,
and problem creation SHALL NOT trigger, queue, or suggest automatic rating.

#### Scenario: Explicit rating request

- **WHEN** the learner asks Pi to rate a bounded set of problems
- **THEN** Pi may check then apply one complete rating manifest through the CLI

#### Scenario: New content remains unrated

- **WHEN** an Agent creates a problem without a separate rating request
- **THEN** the content is ingested with all difficulty fields null

