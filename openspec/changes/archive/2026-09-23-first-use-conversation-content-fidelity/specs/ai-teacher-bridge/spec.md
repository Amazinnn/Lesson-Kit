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
conversation's jobs directory. The server SHALL reject staged paths outside
that directory, impose no fixed six-item limit, validate the full manifest,
create a recoverable backup, and apply one atomic batch. Any invalid item SHALL
produce itemized errors and zero writes; the Agent SHALL repair and resubmit the
complete manifest rather than silently dropping items. Outcomes SHALL remain in
the mirror and next-turn context. Result cards SHALL show batch id, final asset
types/counts, workspace, backup, and current rollback state.

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

## ADDED Requirements

### Requirement: Conversation-owned Pi RPC process

The Bridge SHALL keep one `pi --mode rpc` process per active Pi conversation,
use strict LF-delimited JSONL, send correlated prompt/abort commands, and feed
streamed events into the existing normalized activity contract. The process
SHALL expire after 30 idle minutes; no separate simultaneous-process limit is
imposed. Conversation deletion and server shutdown SHALL close it, while a
later process resumes the saved native session.

One launch or handshake failure before prompt acceptance MAY restart once. A
crash after acceptance SHALL fail the turn without replaying the prompt because
tools may already have caused side effects. Cancellation SHALL send RPC abort
before terminate/kill fallback. All provider child processes SHALL launch
without a visible Windows console.

#### Scenario: Several turns reuse one process

- **WHEN** three serialized turns run in one active Pi conversation
- **THEN** one Pi PID handles all three and native context continues

#### Scenario: Resume after idle expiry

- **WHEN** a Pi process expires after 30 idle minutes and a new turn arrives
- **THEN** a hidden RPC process resumes the saved native session

#### Scenario: Handshake fails once

- **WHEN** Pi fails before accepting the prompt on the first launch
- **THEN** the Bridge restarts once and sends the prompt only after a successful handshake

#### Scenario: Process dies after acceptance

- **WHEN** Pi exits after accepting a prompt and possibly running tools
- **THEN** the turn fails with preserved events and the prompt is not automatically replayed

#### Scenario: Cancel an RPC turn

- **WHEN** the learner stops an active Pi turn
- **THEN** the Bridge sends abort, mirrors no successful exchange, and kills only if abort fails

#### Scenario: Windows providers stay hidden

- **WHEN** any configured provider process starts on Windows
- **THEN** no terminal window becomes visible

