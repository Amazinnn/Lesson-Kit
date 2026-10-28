## MODIFIED Requirements

### Requirement: In-place problem patch
An explicit single-question patch or prevalidated bulk `problem-patch` SHALL reject unknown IDs, unknown fields, cross-course IDs and caller-assigned identity changes. Difficulty SHALL remain a separate command. Metadata/explanation-only and answering-semantically equivalent formatting edits SHALL update in place. Answering-semantic edits SHALL archive the old question and allocate a readable replacement ID, report the mapping, and preserve old evidence and drafts. Practice-mode resolution and touched-field validation SHALL retain existing micro-quiz rules without revalidating untouched legacy fields. Bulk patches SHALL record a readable batch, manifest, previous values, replacement mappings and recoverable backup, and apply atomically. Rollback SHALL restore ordinary patches value for value; replacement rollback SHALL restore the prior active identity and Paper references only when no subsequent dependent learning or content/execution changes would be overwritten, otherwise refuse without writes.

#### Scenario: One problem is edited explicitly
- **WHEN** an explicit patch changes answering semantics
- **THEN** one replacement mapping is reported and old records remain attached to the archived identity

#### Scenario: Ordinary metadata patch
- **WHEN** only explanation, title, provenance, difficulty through its own command, KP associations or semantic-equivalent formatting changes
- **THEN** identity and valid answering progress remain unchanged

#### Scenario: A bulk patch is all or nothing
- **WHEN** any bulk item is invalid
- **THEN** no content, batch, lifecycle or backup state changes and per-item reasons are returned

#### Scenario: A patch is rolled back value for value
- **WHEN** a rollback is valid with no later dependent changes
- **THEN** prior values and active references are restored without deleting learning history

#### Scenario: Unsupported fields are refused
- **WHEN** an unknown field or difficulty field is sent through problem patch
- **THEN** it is rejected with the supported-field list or difficulty-command pointer

### Requirement: Transactional content deletion with historical preservation
Content deletion SHALL be atomic. Problem deletion SHALL archive its identity and content, remove current Paper memberships and default knowledge/search/assembly access, and retain every genuine attempt, feedback, signal, progress, schedule and unsubmitted draft with its original associations. Archived questions SHALL be read-only historical content. Explicit restoration SHALL reactivate that same identity without restoring former Paper membership. Restoring an old replaced question SHALL NOT undo its replacement. Existing KP deletion rules for shared/ownerless problems and relation deletion SHALL remain, with newly ownerless problems following the archive rule. Recoverable Paper publication SHALL coordinate file effects with SQLite. Dependent-evidence rollback refusals SHALL remain.

#### Scenario: Delete a problem with learning records
- **WHEN** a question with attempts and unfinished drafts is explicitly deleted
- **THEN** current references disappear, other item progress survives, and its historical content, records and drafts remain readable

#### Scenario: Restore a superseded question independently
- **WHEN** archived A is restored after B replaced it
- **THEN** A becomes available independently without modifying B or any current Paper

#### Scenario: Delete a knowledge point with shared and ownerless problems
- **WHEN** a KP owns shared and sole-owned problems
- **THEN** shared problems lose only that membership, ownerless problems are archived with history retained, and attached relations are removed atomically

#### Scenario: A deletion step fails
- **WHEN** any transactional archive step fails
- **THEN** no partial lifecycle, progress or publication intent changes remain

### Requirement: Supported content writes coordinate Paper execution invalidation
Explicit patches, content repository synchronization, ingest and governed Agent actions SHALL share one answering-semantic comparison and lifecycle rule. Semantic changes SHALL create replacements; ordinary changes SHALL preserve identities. Every current and archived Paper definition SHALL reconcile its stored references when replaced or when restored, without changing completed history. All writers SHALL preserve affected historical drafts before removing live references. A Paper-only rename or explicit restart SHALL NOT alter question content or ownership. Direct SQL bypasses and arbitrary dependent-history deletion SHALL NOT be authorized.

#### Scenario: The same correction arrives through different writers
- **WHEN** equivalent semantic corrections arrive through supported writers
- **THEN** each reports an old/new mapping and the same affected-item-only restart and stale-submit boundary

#### Scenario: Rename or reset a Paper
- **WHEN** a Paper-only operation renames or explicitly restarts it
- **THEN** question fields and learning evidence remain unchanged

## ADDED Requirements

### Requirement: Replacement inherits learning state exactly once
A replacement SHALL inherit the predecessor's effective question-level learning state and review schedule once at replacement time, but SHALL NOT acquire copied Attempts or verdicts. Later predecessor/successor activity SHALL evolve independently. Historical predecessor evidence SHALL remain available to KP calculations and SHALL count once, even after repeated replacements or independent restoration. No history SHALL be automatically regraded using a new answer key.

#### Scenario: Replace and independently restore
- **WHEN** A becomes B, A is restored, and A receives another answer
- **THEN** B retains its own inherited/evolved state, only A changes from the new answer, and shared past evidence is not duplicated

#### Scenario: Repeat replacement
- **WHEN** B is replaced by C
- **THEN** C inherits B's effective state once and no predecessor Attempt is copied or counted twice
