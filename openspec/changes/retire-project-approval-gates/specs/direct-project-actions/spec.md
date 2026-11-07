## Purpose

Defines the observable 审批与显式批次撤销退役 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.

## ADDED Requirements

### Requirement: Project actions proceed directly

Actions that formerly required project approval SHALL proceed by default after validating actual inputs, without approval cards, extra confirmation clicks, waiting approval states or approval-driven dispatch pauses. Conflict-side choices and unresolved targets SHALL be treated as missing operation input.

#### Scenario: An Agent updates a Paper

- **WHEN** a valid requested existing-Paper change is produced
- **THEN** the change applies without a learner approval click and without an approval pause

#### Scenario: Practice is explicitly restarted

- **WHEN** the learner chooses to start the same Paper over
- **THEN** the requested restart executes directly without an additional approval gate

### Requirement: Legacy pending actions reconcile once

Recovery of a legacy pending approval SHALL revalidate its current target and execution identity and SHALL execute a still-valid unapplied action at most once. Stale callbacks SHALL NOT reapply or target another conversation. Invalid inputs SHALL be reported truthfully.

#### Scenario: An old pending operation is recovered

- **WHEN** the service opens an old pending action during upgrade
- **THEN** the current target is validated and the same action cannot write twice

#### Scenario: A legacy callback arrives

- **WHEN** an obsolete approval callback is repeated after resolution
- **THEN** it cannot repeat the operation or create another approval state

### Requirement: Successful-batch undo is retired

Explicit rollback of successfully applied content batches SHALL be retired from CLI, Agent suggestions and result controls. Ordinary direct repair and data-consistent failed-unit handling SHALL remain available.

#### Scenario: The old command is invoked

- **WHEN** a caller requests successful-batch undo through an old entry
- **THEN** no content is undone and the result identifies direct content repair as the available operation

### Requirement: Ready changes switch without approval

A prepared and verified runtime or data change SHALL perform its normal cutover without waiting for another project approval. It SHALL record actual version identity, migration result and any failed acceptance.

#### Scenario: Prepared update is verified

- **WHEN** backup and isolated migration verification complete for an authorized update
- **THEN** normal cutover proceeds and the installed runtime identity is checked
