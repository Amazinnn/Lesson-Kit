## MODIFIED Requirements

### Requirement: Check ingest action

The bridge SHALL parse a valid governed append-only content action without
depending on message keyword regexes and SHALL execute it automatically without
a confirmation dialog. A reply with no action SHALL perform zero content or
learning writes. Automatic actions MAY add knowledge points, formal problems,
micro quizzes, flash cards, and figures. Updating or deleting existing content,
rolling back a batch, and applying difficulty SHALL still require an explicit
learner instruction. A reply MAY carry several content actions; the bridge SHALL
apply every one of them in order, each with its own validation and its own
batches, so one failing action leaves the others applied and recorded.

Large actions SHALL reference one complete manifest staged under the current
conversation's jobs directory. The server SHALL reject staged paths outside
that directory, impose no fixed six-item limit, validate the full manifest,
create a recoverable backup, and apply one atomic batch. Any invalid item SHALL
produce itemized errors and zero writes; the Agent SHALL repair and resubmit the
complete manifest rather than silently dropping items. Outcomes SHALL remain in
the mirror and next-turn context. Result cards SHALL show batch id, final asset
types/counts, workspace, backup, and current rollback state, and for a bundle
that spans chapters SHALL show every recorded batch with its chapter and its own
rollback state.

Provider file tools MAY read and write arbitrary local paths. Those external
tool writes are outside Lesson Kit's governed batch/rollback boundary. Managed
runtime, pool, staged-manifest, and figure destinations SHALL remain inside the
active workspace.

#### Scenario: Conversation request produces cards

- **WHEN** the Agent returns a valid append-only flash-card action
- **THEN** one governed batch inserts the cards automatically and restores a result card with rollback

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reopened after an action ran or was rolled back
- **THEN** the card reflects the current batch state and an already rolled-back batch has no rollback action

#### Scenario: Gate failure is explicit

- **WHEN** any item in the staged manifest fails validation
- **THEN** every reason is shown, the whole bundle writes nothing, and no success is claimed

#### Scenario: Ordinary conversation cannot ingest

- **WHEN** a provider returns ordinary answer text without a structured action
- **THEN** no content or learning row changes

#### Scenario: Malformed check action is explicit

- **WHEN** a provider returns malformed action JSON or an invalid staged-manifest reference
- **THEN** the conversation shows an explicit contract error and writes nothing

#### Scenario: Rejected manifest is correctable

- **WHEN** the Agent repairs the complete staged manifest from itemized errors
- **THEN** the full bundle is checked anew and may apply under one batch id

#### Scenario: Applied content is not resubmitted

- **WHEN** a prior action applied successfully and another turn starts
- **THEN** the provider receives the batch confirmation and avoids resubmitting the same content

#### Scenario: Examples carry the workspace course

- **WHEN** a content prompt is composed for an active course and chapter
- **THEN** all managed ids, staged paths, and destinations use that workspace scope

#### Scenario: Thirty items form one batch

- **WHEN** one valid staged bundle contains thirty requested problems
- **THEN** the complete list commits under one batch id instead of prompt-driven six-item turns

#### Scenario: Keyword-free follow-up

- **WHEN** the learner says `继续` and the Agent returns another valid append-only action
- **THEN** the action is processed without a keyword-derived intent boolean

#### Scenario: Every content action of one reply is applied

- **WHEN** a reply carries one content action for chapter 12 and another for chapter 13
- **THEN** both are applied in order, each with its own batches, and both results stay in the mirror

#### Scenario: One failing action leaves the others alone

- **WHEN** a reply carries two content actions and the second fails validation
- **THEN** the first is applied and recorded, the second writes nothing, and its itemized reasons reach the learner and the next turn

#### Scenario: A multi-chapter bundle reports each batch

- **WHEN** an applied bundle contains content for two chapters
- **THEN** the result lists both batches with their chapters and counts, and each card row offers its own rollback

### Requirement: Action block disclosure

A provider reply MAY carry multiple lessonkit-action blocks. The bridge SHALL
consider every block: every content block SHALL be applied, and an
intent-gated block SHALL be applied only for its active intent. Applying several
content blocks SHALL NOT be treated as a conflict. When a reply carries action
blocks but none is accepted, the bridge SHALL strip the blocks from the mirrored
answer, record that they were ignored with the reason, and carry that disclosure
into the next turn's provider context so the agent does not claim writes that
never happened.
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

#### Scenario: Several content blocks all land

- **WHEN** a reply carries three content manifests, one per chapter
- **THEN** all three are applied in the order they appear and none is dropped silently
