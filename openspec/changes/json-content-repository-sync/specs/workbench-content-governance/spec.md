## ADDED Requirements

### Requirement: Version-controlled JSON projection of governed course content

Lesson Kit SHALL support a checked-out repository that stores governed authored course content as strict UTF-8 JSON, independently of the physical workspace directory. One repository MAY contain multiple courses under `courses/<course-id>/`; synchronization of one workspace SHALL read only the directory for that workspace's Course Identifier plus deletion requests that explicitly target that course.

For the initial supported projection, each knowledge point, durable problem, and knowledge relation SHALL be represented by one entity JSON object with exactly these envelope fields: `schema_version`, `entity_type`, `entity_id`, `revision`, and `content`. The entity id SHALL be the semantic identity. Moving or renaming the file SHALL NOT change identity, and changing `entity_id` in place SHALL be rejected as an identity change rather than treated as a rename.

The v1 projection SHALL contain authored fields only. It SHALL support knowledge points, durable problems, and knowledge relations. It SHALL NOT support flash-card entities, figure bytes, or specialized problem-difficulty fields. Repository-only entity creation SHALL be refused. Learner/runtime state including attempts, progress, feedback, schedules, learner signals, session state, caches, and derived statistics SHALL NOT be exported to the repository.

No hash value, fingerprint, SHA value, or content-derived id SHALL be introduced for synchronization.

#### Scenario: Two physically different workspaces synchronize by course id

- **GIVEN** two registered workspaces live at unrelated local paths
- **AND** their Course Identifiers are different
- **WHEN** each is synchronized against the same checked-out content repository
- **THEN** each reads and writes only its own `courses/<course-id>/` subtree, regardless of the workspace folder name or location

#### Scenario: Renaming a JSON file does not rename the entity

- **GIVEN** an entity file is moved within the same course subtree without changing its envelope
- **WHEN** synchronization runs
- **THEN** the same pool entity is compared and no create/delete operation is inferred from the path move

#### Scenario: Runtime learning state is not exported

- **GIVEN** a durable problem has attempts, feedback, schedule, progress, and learner signals
- **WHEN** its repository JSON is written
- **THEN** none of those runtime rows appears in the entity JSON

### Requirement: Integer revision and normalized-content synchronization

Each mirrored entity SHALL carry a positive integer `revision`. The pool SHALL remember the last synchronized revision and the last synchronized normalized authored `content` for each tracked entity. Synchronization SHALL compare the current pool projection and repository payload against that remembered content; it SHALL NOT use hashes to detect change.

For a repository-originated edit of a tracked entity, the file revision SHALL equal the remembered revision plus one. A changed payload with an unchanged revision, a lower revision, or a revision jump greater than one SHALL be invalid and SHALL cause zero content writes for that entity.

When exactly one side changed from the remembered content, synchronization SHALL propagate that side. When both sides changed to different authored content, synchronization SHALL report a conflict and SHALL NOT silently choose a winner. When both sides independently reached the same authored content, synchronization MAY record the converged revision without rewriting the content.

Rollback of authored content SHALL be a new forward revision containing the older desired payload; revision numbers SHALL never decrement.

#### Scenario: Repository edit advances one revision

- **GIVEN** the remembered revision is 6 and the pool still equals the remembered content
- **AND** the repository file carries revision 7 with a valid changed payload
- **WHEN** synchronization runs
- **THEN** the governed pool mutation is applied and revision 7 becomes the remembered synchronized state

#### Scenario: Changed content without a revision bump is refused

- **GIVEN** the remembered revision and repository revision are both 6
- **AND** the repository `content` differs from the remembered content
- **WHEN** synchronization runs
- **THEN** that entity is reported invalid and neither side is overwritten

#### Scenario: Concurrent semantic edits are not merged silently

- **GIVEN** the pool and repository both differ from the remembered content
- **AND** their current authored payloads differ from each other
- **WHEN** synchronization runs
- **THEN** that entity is reported as a conflict with zero writes for that entity

### Requirement: Explicit pool-first bootstrap

Lesson Kit SHALL provide an explicit bootstrap operation that establishes initial repository ancestry from an existing knowledge pool. Bootstrap SHALL export every supported pool entity for the selected course at revision 1 and SHALL remember the same normalized authored content at revision 1.

Bootstrap SHALL be resumable per entity. It SHALL NOT overwrite an existing entity file whose semantic envelope/content disagrees with the pool. A later bootstrap run SHALL skip already-established matching entities and continue uninitialized entities.

#### Scenario: Existing course becomes a repository projection

- **GIVEN** an existing course pool has knowledge points, durable problems, and relations and has no mirror state
- **WHEN** the user bootstraps that workspace into an empty course subtree
- **THEN** one JSON file per supported entity is written at revision 1 and matching revision/content state is recorded in the pool

#### Scenario: Bootstrap finds independently authored conflicting JSON

- **GIVEN** an untracked pool entity and an existing JSON file name the same entity id but hold different authored content
- **WHEN** bootstrap reaches that entity
- **THEN** that entity is refused rather than choosing either copy, while independently successful entities remain bootstrapped

### Requirement: Per-entity atomic synchronization with partial course success

The synchronization transaction boundary SHALL be one content entity. A course-level run MAY partially succeed: successful entities remain synchronized even when another entity is invalid, conflicting, or temporarily blocked by a missing reference.

Each repository-to-pool entity write SHALL first produce the normalized projection returned by the existing governed validator for that entity. Planning and convergence checks SHALL compare that normalized projection with the pool and remembered content. After a successful repository edit, the JSON envelope SHALL be rewritten with the normalized content at the same revision.

The content mutation, remembered revision/content update, and success-log row for a repository-to-pool edit SHALL commit in one SQLite transaction. If validation, mutation, or ledger writing fails, the entity content and mirror state SHALL remain unchanged. The normalized JSON rewrite SHALL occur in an order that permits a retry after interruption without losing the edit.

#### Scenario: One bad entity does not roll back unrelated good entities

- **GIVEN** a run contains two independent repository edits
- **AND** one passes its existing content contract while the other fails validation
- **WHEN** synchronization runs
- **THEN** the valid entity is synchronized atomically, the invalid entity is unchanged, and the report contains both outcomes

#### Scenario: Reference dependency is retried

- **GIVEN** a repository file names an entity that does not exist in the pool
- **WHEN** synchronization runs
- **THEN** that repository-only entity is refused without allocating an id or writing pool content

#### Scenario: Normalized repository edits converge atomically

- **GIVEN** a tracked problem has `exam_year` set to `2022`
- **AND** its next repository revision changes `exam_year` to the accepted empty value
- **WHEN** synchronization applies the edit
- **THEN** the pool, mirror ledger, and rewritten repository envelope all store the normalized empty value
- **AND** if the mirror ledger write fails, the pool retains `2022` and the prior ledger revision

### Requirement: Repository absence and deletion requests never delete pool content

A missing repository entity file SHALL NOT be interpreted as deletion. For a tracked entity whose pool row still exists, synchronization SHALL restore the repository file from the pool as a new revision rather than deleting the pool row.

The repository MAY contain explicit deletion-request JSON documents. The mirror command SHALL validate and report such requests but SHALL NOT call a pool content-delete path because of them. If a tracked pool row is physically absent, synchronization SHALL report a conflict requiring a separate explicit local decision.

#### Scenario: Accidental Git-side file deletion is harmless to the pool

- **GIVEN** a tracked entity file is absent from the checked-out repository but its pool row still exists
- **WHEN** synchronization runs
- **THEN** the pool row and all runtime history remain intact and the repository entity is restored as a forward revision

#### Scenario: Explicit deletion request is non-executing

- **GIVEN** a valid deletion-request JSON names an existing durable problem
- **WHEN** synchronization runs
- **THEN** the request is reported as pending/non-executed and the durable problem remains unchanged

### Requirement: Read-only validation and dry-run surface

The CLI SHALL expose a `mirror` command group over a registered workspace and local repository checkout. It SHALL provide bootstrap, validation/status, synchronization, and dry-run behavior without performing Git network/authentication operations.

`check`, `status`, and `sync --dry-run` SHALL perform zero pool-content writes and zero entity-file writes. Their machine-readable report SHALL classify entities sufficiently to distinguish at least: no change, repository-to-pool, pool-to-repository, repository restoration, converged recovery, invalid, and conflict.

The command SHALL support restricting work to one entity id so interrupted or high-risk changes can be inspected and resumed precisely.

#### Scenario: Dry run and real sync share the same plan

- **GIVEN** neither side changes between commands
- **WHEN** the user runs `mirror ... sync --dry-run` and then `mirror ... sync`
- **THEN** the first command writes nothing and reports the same intended per-entity directions the second command subsequently executes

#### Scenario: Mirror command does not manage Git transport

- **WHEN** any mirror command runs
- **THEN** it reads/writes the supplied local checkout only and does not invoke `git pull`, `git commit`, or `git push`
