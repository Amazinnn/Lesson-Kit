## Purpose

Defines the observable 完整课程交换与外部 Tutor 交接 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.

## ADDED Requirements

### Requirement: Complete portable course assets

A Course Exchange Bundle SHALL cover every managed course content, source attachment, Paper, learning fact, unfinished draft, non-sensitive preference and Course Learning File listed in the exchange matrix. The default full-course operation SHALL disclose unsupported or missing assets and SHALL NOT report complete success while any required class is absent.

#### Scenario: All asset classes round trip

- **WHEN** a complete course is exported and received in a new installation using files alone
- **THEN** all managed classes, original text and bytes are preserved and the saved Paper can continue

#### Scenario: Teaching context is portable

- **WHEN** an external Tutor receives the declared course files
- **THEN** goals, resources, demonstrated-understanding evidence, corrected misconceptions and teaching position are readable and its returned updates can be received

### Requirement: Governed file CRUD and identity

The receiver SHALL support additions, updates, explicit deletions and restoration, validate course origin and dependencies, and register a genuinely new course in one receive operation. A missing file alone SHALL NOT authorize deletion.

#### Scenario: New course is registered

- **WHEN** the target has no course registration
- **THEN** one receive operation validates and registers the course and reports required configuration

#### Scenario: Existing untracked course needs association input

- **WHEN** a registered nonempty course has no proven shared origin with the received package
- **THEN** receiving requires explicit association input or a separate new target and never silently adopts the package origin

#### Scenario: Deletion and modification conflict

- **WHEN** one side explicitly deletes an entity and the other modifies it after the shared base
- **THEN** the entity requires conflict-side input and independent valid units can complete

#### Scenario: Missing file is incomplete transport

- **WHEN** a managed entity file disappears without a deletion record
- **THEN** the receiver reports absence and retains the existing entity

### Requirement: Reconcile versions and learning facts

One-sided and identical changes SHALL reconcile automatically. Genuine two-sided changes SHALL expose differences and accept a single or batch side choice. Independent attempt facts SHALL merge without duplication. Different-question draft updates SHALL merge while same-question differences require side choice.

#### Scenario: Independent histories are united

- **WHEN** both installations add distinct attempts
- **THEN** both sets persist exactly once through repeated exchange

#### Scenario: Drafts merge by question

- **WHEN** two installations modify different questions of the same unfinished Paper
- **THEN** both changes survive and only genuinely conflicting question drafts need side selection

### Requirement: Partial completion is recoverable

The receiver SHALL apply Independent Valid Mutation Units, retain invalid items and their dependents, and report actual per-item outcomes. Retrying interrupted input SHALL NOT duplicate completed facts or re-execute accepted operations. Explicit successful-batch undo SHALL be retired.

#### Scenario: Invalid dependency is isolated

- **WHEN** valid independent items accompany an invalid reference
- **THEN** valid units complete while the invalid dependency group stays unchanged

#### Scenario: Crashed writer does not leave permanent lock ownership

- **WHEN** an exchange process exits abnormally while owning the course write lock
- **THEN** a later exchange can acquire ownership without guessing PID liveness or deleting another owner's lock

#### Scenario: Interrupted reception is retried

- **WHEN** the process stops at a publication boundary and the same input is received again
- **THEN** completed identities are reconciled and unfinished units complete without duplicate records

#### Scenario: Local data changes after inspection

- **WHEN** confirmed local data changes after a receive inspection and before its write transaction
- **THEN** stale writes are refused for a fresh inspection and the newer local answer or draft is preserved

#### Scenario: One file cannot be published

- **WHEN** an accepted file cannot be atomically published while other incoming units are independent
- **THEN** independent units complete, the file remains explicitly pending for retry, and newer updates to that same file do not erase its unfinished publication

### Requirement: Git transport and hourly scheduling

The same configured CLI SHALL coordinate file exchange and Git transport and SHALL support hourly operating-system scheduling for all registered courses with configured media. A quiet success and a single short conflict notification SHALL reflect actual outcomes. Git publication SHALL be reported independently from local reception.

#### Scenario: Remote publication fails

- **WHEN** local coordination succeeds but push is rejected
- **THEN** the receipt identifies local completion and unpublished changes without claiming remote success

#### Scenario: Configured courses are scheduled

- **WHEN** the hourly task runs while one configured course conflicts
- **THEN** independent courses complete, the conflict remains unresolved and a single short notification is issued

### Requirement: External Tutor input and output preserve learning truth

External Tutor Handoff SHALL carry original question and answer identities, unanswered items, reveal facts, goals and continuation position. Receiving Tutor output SHALL preserve raw learner answers and distinguish interpretations from observed facts.

#### Scenario: Answers were revealed before sending

- **WHEN** a learner reveals answers and sends the results
- **THEN** the Tutor receives original learner choices and reveal facts rather than replacement correct answers

#### Scenario: Learning preferences are consumed

- **WHEN** saved preferences travel with the course files
- **THEN** the receiving normal practice entry uses the received submission and reveal preferences

### Requirement: Tutor file additions use the ordinary return path

A newly added ordinary file under the readable files tree SHALL declare a new safe course file identity without manual manifest editing. A missing readable file SHALL NOT authorize deletion. Excluded runtime, credentials and database paths SHALL remain protected, and a readable file SHALL NOT bypass an invalid declared envelope.

#### Scenario: Tutor returns a new learning note

- **WHEN** an external Tutor adds a new learning Markdown file under the package files tree
- **THEN** the same receive command saves the exact text and later export carries it onward while preserving original learner attempts

#### Scenario: New course creation validates input first

- **WHEN** a new workspace is received with an explicit new target directory
- **THEN** package and course identity validation precede creation and registration, and invalid input leaves no target or registration

### Requirement: Retained Paper item history travels with the course

The Paper item history kept for removed questions SHALL be a managed course asset: exported with its Paper, receivable into a target that has not migrated the table yet, and carried on by the next exchange. Two installations SHALL be able to number their own history for the same Paper without one silently replacing the other: the asset identity carries the installation origin, a received row takes the next local sequence, and a repeated reception appends nothing. A historical reference to a fact this course no longer holds SHALL be reported and left empty rather than making the package unexportable, and no local record may be bound merely because its number matches.

#### Scenario: History survives the first hop and the next one

- **WHEN** a Paper with a removed question is exported, received, continued and exported again
- **THEN** the retained row, its last saved draft and the surviving item states match at every hop

#### Scenario: Two installations append their own history

- **WHEN** both installations already hold a retired item numbered 1 for the same Paper
- **THEN** both facts persist under the receiver's own numbering and neither row is overwritten

#### Scenario: A historical reference no longer resolves

- **WHEN** a retained row points at an attempt this course no longer holds
- **THEN** the package still exports, the receipt reports the unresolved reference, and no local attempt is bound in its place

### Requirement: A repeated operation returns its original result

An executed request replayed on another installation SHALL be recognised by its request identity and return the original result without writing again. The same request identity carrying different content SHALL remain a genuine conflict. Historical display data SHALL keep the source installation's numbers as opaque values, while an operational reference that cannot be resolved SHALL be reported instead of being bound to a coincidentally equal local record. A feedback event referenced only by a historical snapshot SHALL NOT block export.

#### Scenario: The same request is replayed after the course moves

- **WHEN** installation B repeats a request executed on A and the course later returns to A
- **THEN** each replay returns the original receipt and adds no attempt, draft or event

#### Scenario: Different content under the same request identity

- **WHEN** a request identity arrives with different content
- **THEN** the receiver reports a real conflict instead of replaying

#### Scenario: The referenced feedback was deleted

- **WHEN** a historical snapshot points at a feedback event that no longer exists
- **THEN** export still completes, reports the unresolved reference, and keeps the snapshot text unchanged
