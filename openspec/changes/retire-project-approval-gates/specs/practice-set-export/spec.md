## MODIFIED Requirements

### Requirement: Saved Paper updates preserve container identity

Updates explicitly targeting an existing Paper SHALL retain Paper ID. Title/description-only and no-op changes SHALL retain unfinished execution state. Membership/order updates SHALL apply directly without extra approval and SHALL preserve unaffected items' progress and drafts through the content lifecycle. Removed or changed items SHALL be coordinated explicitly without modifying historical attempts, ratings or unrelated Papers. Saving SHALL NOT start practice automatically. Legacy rejected or obsolete callbacks SHALL perform no write.

#### Scenario: Update the original Paper instead of creating another

- **WHEN** a valid requested membership or order update targets a partially practiced saved Paper
- **THEN** the same Paper is updated directly and unaffected progress, questions, learning evidence and other Papers remain

#### Scenario: Rename without resetting practice
- **WHEN** only a saved Paper's title or description changes
- **THEN** its unfinished state, drafts and item order remain unchanged

#### Scenario: Cancel a structure change

- **WHEN** a rejected legacy operation or obsolete callback is received
- **THEN** the obsolete input performs no write and does not create another approval gate

