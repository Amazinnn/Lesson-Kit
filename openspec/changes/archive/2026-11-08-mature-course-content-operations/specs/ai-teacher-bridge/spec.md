
## MODIFIED Requirements

### Requirement: Check ingest action

The Bridge SHALL parse governed content action blocks and execute valid requested or persistently authorized operations without a project approval dialog. Ordinary text without a structured action SHALL write no content or learning facts. Automatic content actions can add knowledge points, formal problems, micro quizzes, flash cards and figures. Existing-content edits and difficulty writes SHALL remain bound to actual user intent or scoped ongoing authorization. Explicit successful-batch undo SHALL be retired.

Staged paths SHALL remain within the owning conversation. Inline kind/type content-bundle SHALL use the same contract. Every item SHALL resolve its own valid chapter or a valid manifest chapter, never the active page chapter. Independent dependency-complete units SHALL be validated and applied consistently with backup and readable per-chapter provenance. Invalid units and dependents retain prior state while independent valid units complete. Outcomes SHALL truthfully reach the conversation mirror and next-turn context, with no success claim for failed content. Completed identities SHALL not be resubmitted as new content.

The Agent SHALL continue requested chapters without another redundant user approval or continue prompt. Default UI result presentation SHALL be concise and SHALL NOT add source, reason, rollback-state fields or rollback controls. Full CLI and verification receipts SHALL preserve detailed actual outcomes. External provider file tools keep their existing scope, while managed runtime/pool/staged/figure destinations remain bounded by the active workspace.

#### Scenario: Conversation request produces cards

- **WHEN** the Agent returns a valid append-only flash-card action
- **THEN** valid independent units insert the cards directly and the result reflects actual completion without rollback controls

#### Scenario: Result card survives re-render

- **WHEN** the conversation is reopened after an action ran or was rolled back
- **THEN** the actual recorded result is restored once without rollback actions or new default explanation fields

#### Scenario: Gate failure is explicit

- **WHEN** any item in the staged manifest fails validation
- **THEN** invalid units and their dependents remain unchanged, independent valid units may complete, and the mirror records actual itemized outcomes without claiming complete success

#### Scenario: Ordinary conversation cannot ingest

- **WHEN** a provider returns ordinary answer text without a structured action
- **THEN** no content or learning row changes

#### Scenario: Malformed check action is explicit

- **WHEN** a provider returns malformed action JSON or an invalid staged-manifest reference
- **THEN** the conversation shows an explicit contract error and writes nothing

#### Scenario: Rejected manifest is correctable

- **WHEN** the Agent repairs the complete staged manifest from itemized errors
- **THEN** corrected units are checked and applied while completed identities are reconciled without duplication

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
- **THEN** the receipt lists both chapter batches and counts, and normal result cards contain no rollback action

#### Scenario: One reply imports several chapters

- **WHEN** a learner asks for three chapters and the Agent answers with one manifest spanning them, or with one content block per chapter
- **THEN** every chapter is written in that turn, one batch per chapter, and no further learner message is required to finish the request

#### Scenario: An inline manifest is accepted

- **WHEN** a reply carries a small inline manifest whose block declares `type` as `content-bundle`
- **THEN** the manifest is applied exactly as the staged form, with no contract error

#### Scenario: A chapter-less item is refused with its label

- **WHEN** a manifest has no bundle-level chapter and an item declares none, even though the workspace has an active chapter
- **THEN** the affected dependency unit stays unchanged, its missing chapter is recorded, and independent valid units can complete

#### Scenario: Stopping early is corrected next turn

- **WHEN** an import applied successfully for some of the chapters the learner asked for
- **THEN** the next-turn context states the applied batches and tells the Agent to continue the remaining chapters without waiting for another learner message

