## MODIFIED Requirements

### Requirement: Legacy pending actions reconcile once

Recovery of a legacy pending approval SHALL revalidate its current target and execution identity and SHALL execute a still-valid unapplied action at most once. Stale callbacks SHALL NOT reapply or target another conversation. Invalid inputs SHALL be reported truthfully.

#### Scenario: An old pending operation is recovered

- **WHEN** the service opens an old pending action during upgrade
- **THEN** the current target is validated and the same action cannot write twice

#### Scenario: A legacy callback arrives

- **WHEN** an obsolete approval callback is repeated after resolution
- **THEN** it cannot repeat the operation or create another approval state

#### Scenario: Recovery encounters an operational error

- **WHEN** preview or execution of a still-pending legacy action encounters a temporary operational error
- **THEN** recovery reports the error without changing the action to invalid; a later normal recovery revalidates the original action and cannot execute it twice
