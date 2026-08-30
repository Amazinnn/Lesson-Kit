## ADDED Requirements

### Requirement: Action block disclosure

A provider reply MAY carry multiple lessonkit-action blocks. The bridge SHALL
consider every block and apply the first one matching the active intent, not
only the first block in the reply. When a reply carries action blocks but none
is accepted, the bridge SHALL strip the blocks from the mirrored answer, record
that they were ignored with the reason, and carry that disclosure into the next
turn's provider context so the agent does not claim writes that never happened.
A block that matches an active intent but is discarded by its own field
contract (for example a goal form without a usable title) stays silently
discarded per that contract.

#### Scenario: A later matching block is not shadowed

- **WHEN** a reply under content-generation intent carries a practice-selection
  block followed by a bare flash-card manifest
- **THEN** the manifest is extracted and applied, and the earlier
  non-matching block does not shadow it

#### Scenario: Blocks without matching intent are disclosed

- **WHEN** a reply contains lessonkit-action blocks and no block matches the
  active intents
- **THEN** the blocks are removed from the mirrored answer, the turn records
  the ignored disclosure, nothing is written, and the next turn's provider
  context states that no write happened
