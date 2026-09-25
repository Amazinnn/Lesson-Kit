## MODIFIED Requirements

### Requirement: Check ingest action

The bridge SHALL parse a valid governed append-only content action without
depending on message keyword regexes and SHALL execute it automatically without
a confirmation dialog. A reply with no action SHALL perform zero content or
learning writes. Automatic actions MAY add knowledge points, formal problems,
micro quizzes, flash cards, and figures. Updating or deleting existing content,
rolling back a batch, and applying difficulty SHALL still require an explicit
learner instruction.

Large actions SHALL reference one complete manifest staged under the current
conversation's jobs directory. An inline manifest SHALL be accepted whether it
declares its `kind` or its `type` as `content-bundle`. The server SHALL reject
staged paths outside that directory, impose no fixed item ceiling, validate the
full manifest, create a recoverable backup, and apply one transaction. One
manifest MAY span several chapters: every knowledge point, problem, and flash
card SHALL resolve exactly one chapter (its own `chapter`, else the manifest's), a
manifest that leaves any item without a chapter SHALL be refused with that item's
label instead of falling back to the workspace chapter, and every derived value —
allocated id prefix, figure destination, micro-quiz id, duplicate check — SHALL
follow the item's chapter. The apply SHALL record one batch per chapter present,
so a chapter can be rolled back on its own, while prevalidation, backup, and the
transaction cover the whole manifest. Every content action block in one reply
SHALL be applied in order, so a learner who asks for several chapters is served
in one turn. Any invalid item SHALL produce itemized errors and zero writes; the
Agent SHALL repair and resubmit the complete manifest rather than silently
dropping items. Outcomes SHALL remain in the mirror and next-turn context, where
a successful apply SHALL also tell the Agent to continue any chapters the learner
asked for that are still missing rather than asking the learner for another
「继续」. Result cards SHALL show batch id, final asset types/counts, workspace,
backup, and current rollback state.

Provider file tools MAY read and write arbitrary local paths. Those external
tool writes are outside Lesson Kit's governed batch/rollback boundary. Managed
runtime, pool, staged-manifest, and figure destinations SHALL remain inside the
active workspace.

#### Scenario: Conversation request produces cards

- **WHEN** the Agent returns a valid append-only flash-card action
- **THEN** one governed batch inserts the cards automatically and restores a result card with rollback

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reopened after an action ran or was rolled back
- **THEN** the card reflects the current batch state and an already rolled-back batch has no rollback action, and a turn carrying one action renders one card

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

#### Scenario: One reply imports several chapters

- **WHEN** a learner asks for three chapters and the Agent answers with one manifest spanning them, or with one content block per chapter
- **THEN** every chapter is written in that turn, one batch per chapter, and no further learner message is required to finish the request

#### Scenario: An inline manifest is accepted

- **WHEN** a reply carries a small inline manifest whose block declares `type` as `content-bundle`
- **THEN** the manifest is applied exactly as the staged form, with no contract error

#### Scenario: A chapter-less item is refused with its label

- **WHEN** a manifest has no bundle-level chapter and an item declares none, even though the workspace has an active chapter
- **THEN** that item is refused with its label and a reason that names the missing chapter, and nothing is written

#### Scenario: Stopping early is corrected next turn

- **WHEN** an import applied successfully for some of the chapters the learner asked for
- **THEN** the next-turn context states the applied batches and tells the Agent to continue the remaining chapters without waiting for another learner message
