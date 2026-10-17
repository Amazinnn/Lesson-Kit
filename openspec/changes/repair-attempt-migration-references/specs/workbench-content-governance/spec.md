## ADDED Requirements

### Requirement: Attempt schema migration preserves inbound references
Widening or repairing attempt schema SHALL preserve existing attempt IDs/values, surviving child rows and unrelated schema objects, and SHALL leave inbound foreign keys targeting the intended persistent parent rather than a dropped temporary table. Rerunning migration on a healthy current schema SHALL be idempotent. Already-misbound legacy declarations SHALL be detected even when the parent status constraint is already current. Healthy isolated fixtures SHALL pass foreign-key validation. Missing-parent data SHALL be reported explicitly without fabricating parents or deleting surviving child progress to obtain a clean check.

#### Scenario: Widen a legacy parent with nonempty children
- **WHEN** answered-status migration runs on a healthy old attempt table with referencing progress rows
- **THEN** all original attempts/child values survive, references target the final attempt table, and foreign-key validation passes

#### Scenario: Repair an already-misbound legacy child
- **WHEN** a child declaration points to nonexistent `problem_attempts_widening_old` but the intended parent rows survive
- **THEN** the declaration is repaired without losing rows and a second run makes no further data/schema change

#### Scenario: Intended parent rows are also missing
- **WHEN** structural repair encounters surviving child rows whose intended attempts no longer exist
- **THEN** surviving rows are preserved, unresolved references are reported, and the result does not claim historical evidence was recovered or integrity fully restored
