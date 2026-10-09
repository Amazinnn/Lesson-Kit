# Targeted schema restoration

Reuse PR106's SQLite `ALTER TABLE problems DROP COLUMN topic_label` for an
already-current problem table. Remove the field from the existing legacy
rebuild DDL and copy list so a rebuild never introduces or retains it. Leave
unrelated schema migrations unchanged.

The operator first creates a SQLite recovery backup outside the live database,
then proves the column drop and recovery on copies. With the live database
locked in a transaction, remove only the observed c05
`problems_by_chapter` view's `p.topic_label` projection, preserving its remaining
SQL, and drop the target column. Preserve all other objects and rows. Any
additional dependency is an explicit blocker, not permission to drop it.
Do not replace live database files or WAL files. Do not invoke general schema
ensure for this targeted live deletion.

Backups retain the old values outside the migrated schema. Current databases
have no replacement column or retention table. Flash-card labels are unchanged.

Focused tests cover legacy rebuild, current-shape deletion, all nontarget values
and learning rows, foreign keys, flash cards, repeated ensure, and recovery from
an external SQLite backup. A separate reviewer owns final acceptance.
