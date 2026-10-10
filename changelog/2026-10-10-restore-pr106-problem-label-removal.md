# Restore PR106 physical problem-label removal

The ordinary-ensure retention policy introduced by PR111 contradicted PR106.
It is superseded: current schemas physically omit `problems.topic_label`,
including legacy table rebuilds. Flash-card labels keep their existing contract.
No replacement column/table stores the retired problem values.

## Actual registered database deployment

On 2026-10-10, all 17 registered course databases were backed up through SQLite
into `C:\Users\yanwei\.lessonkit-workbench\backups\pr106-topic-removal-20261010-001`.
The external `manifest.json` identifies every source, recovery backup and outcome.
Migration and full recovery were proved on copies before touching live databases.

All 17 live migrations completed. Each database used a write reservation and
transaction; the current full recovery backup was verified before deletion.
Every other table column and row value was compared before commit, together
with unrelated SQLite objects, integrity and foreign-key state. The c05
`problems_by_chapter` view lost only its direct `p.topic_label` projection.
Historical labels remain recoverable from external old-database backups.

The operator refuses an unprepared dependent view and refuses to refresh a
backup when a committed migration is missing from the manifest. Independent
fixtures verified rollback and interruption recovery safety.

## Runtime and verification

The installed editable `lesson-kit` now resolves to the verified
`.worktrees/restore-topic-removal-20261010` checkout. The original dirty source
checkout was preserved; its older Python scripts are not the deployment entry.
No dependencies or provider settings were changed.

Independent repository validation: 881 Python tests, 140 Node tests, compile,
14 strict live specs, strict change validation and dmath/ch06 extract guard
passed. Independent post-deployment read-only acceptance is recorded below.

PR110 and the existing deferred defect registers remain outside this correction.

Independent post-deployment acceptance passed for all 17 actual databases:
target column absent; all other full table rows/columns and unrelated SQLite
objects match the external backup; integrity and foreign-key state unchanged.
All 66 existing flash-card rows and their label values were preserved. The c05
view columns and full projected results also match after removing only the
target column. All backups still contain the retired column and original values.
Installed console entry and `lesson-kit --help` were independently verified
from a neutral working directory. No manual UI acceptance is claimed for this
schema-only correction.

Verified totals: 15,769 problem rows remain unchanged apart from the removed
column; 15,696 populated old labels remain recoverable in the backups.
The OpenSpec CLI archived the completed change on 2026-10-10 and reported
that its live spec was already synchronized.
