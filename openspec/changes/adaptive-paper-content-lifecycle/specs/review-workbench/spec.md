## MODIFIED Requirements

### Requirement: Durable practice run archive

The single active-practice resource SHALL remain the execution authority for one
Paper-backed Practice Run. Every newly created execution SHALL use the product
source semantic `paper`; historical `quick`, `practice_set`, or `agent` source
values MAY remain readable as migration data, and replaying such history SHALL
create a new Paper-sourced execution. Saved-Paper replay SHALL use its current available membership and latest content; original archived items SHALL remain historical evidence. Temporary-Paper replay SHALL resolve only available current identities and report unavailable ones without resurrecting archived questions.

When the learner explicitly submits the Paper, or a run is explicitly replaced or cleared, the workbench SHALL
append one minimal `practice_runs` snapshot before deleting active execution
state. The snapshot SHALL preserve Paper source identity/reference/label, ordered
item identities and final states, rating compatibility metadata, timestamps, and the submitted per-item answer references and presentation state needed to reopen the completed answer sheet. It SHALL NOT replace, duplicate, edit, or delete `problem_attempts` or
`feedback_events`.

#### Scenario: Completing the last item archives the run

- **GIVEN** the learner has explicitly requested final Paper submission
- **WHEN** the final pending item of an active Paper is answered or marked stuck
- **THEN** one completed snapshot is appended and active execution is cleared exactly once as part of that explicit submission
- **AND** answering the last item outside explicit final submission does not archive the run

#### Scenario: Replacing an unfinished run keeps both histories honest

- **WHEN** the learner explicitly replaces an unfinished Paper run
- **THEN** the old run is archived as abandoned, its existing attempts remain unchanged, and the new Paper starts independently

#### Scenario: Replay legacy history through the Paper boundary

- **WHEN** a historical run labelled `quick`, `practice_set`, or `agent` is replayed
- **THEN** the new execution stores the Paper source semantic, uses current membership for a saved Paper, and retains the old archived items only as historical evidence

### Requirement: Question corrections reset only affected unfinished items
Answering-semantic corrections SHALL archive the old identity and substitute a new identity at each current Paper position. Only the replacement item SHALL become pending; prior draft and Attempt links SHALL remain available in historical records. All other items SHALL retain progress. Explanation/title/KP/difficulty/provenance-only, no-op and answering-equivalent formatting changes SHALL NOT reset execution state. Historical verdicts SHALL NOT be regraded. Writes against superseded identity, structure, revision or position SHALL fail before learning writes, without silently translating an old answer to the new item.

#### Scenario: Correct a shared question's answer key
- **WHEN** Q occurs in unfinished A/B and its answer key changes
- **THEN** its replacement is pending in A/B, old Q drafts and evidence remain historical, and other items retain progress

#### Scenario: Edit only explanation or metadata
- **WHEN** only ordinary metadata or equivalent formatting changes
- **THEN** completion/drafts remain and a current answer is not rejected solely for that revision

#### Scenario: Old page submits after correction
- **WHEN** a stale page submits after semantic or structural changes
- **THEN** it receives an explicit recoverable conflict without an Attempt or learning effect

### Requirement: Question deletion preserves unrelated execution progress and history
Question archive SHALL remove current memberships and unfinished references after preserving their historical draft/answer associations. It SHALL preserve every other item's execution state and all learning history. The same retention rule SHALL apply to ordinary membership/order edits rather than being an exception to full reset. The cursor SHALL follow its surviving identity, else the next survivor, else the preceding survivor. Removing the last item SHALL retain an empty unfinished Paper without fabricated completion.

#### Scenario: Delete a question shared by multiple unfinished Papers
- **WHEN** Q is archived while A/B reference it
- **THEN** Q leaves both live lists, its old drafts remain readable, and all other progress and evidence survive

## ADDED Requirements

### Requirement: Derived learning results refresh on demand
Only derived results whose actual dependencies changed SHALL be marked stale. A stale result SHALL be refreshed before display or use in assembly, state, weakness or scheduling decisions; unused results SHALL remain stale without background recomputation. Reads of unaffected values SHALL retain their results. Failed refresh SHALL report failure rather than present or use an old value as current. Archive SHALL NOT erase historical learning contributions; replacement inheritance SHALL survive later refresh without double-counting evidence or regrading historical verdicts.

#### Scenario: Mark now and calculate when used
- **WHEN** a content mutation affects Paper statistics and a KP result but nobody reads the KP result
- **THEN** affected persisted results are stale, only requested statistics are refreshed, and no global recomputation runs

#### Scenario: Update fails or races
- **WHEN** refresh fails or dependencies change before its publication
- **THEN** it does not publish a current result for outdated dependencies and the reader receives an explicit failure/conflict

#### Scenario: Archive preserves actual knowledge evidence
- **WHEN** an answered question is archived and KP learning results are next used
- **THEN** its historical evidence still contributes once while available-question counts exclude it
