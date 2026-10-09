## RENAMED Requirements

- FROM: `### Requirement: Preserve retired problem-label history during ordinary schema ensure`
- TO: `### Requirement: Remove retired problem labels from current schemas`

## MODIFIED Requirements

### Requirement: Remove retired problem labels from current schemas

Workbench schema ensure SHALL physically remove an existing
`problems.topic_label` column, and a rebuilt problem table SHALL omit that
column. This requirement explicitly supersedes the previous ordinary-ensure
retention semantics introduced after PR106. Current databases SHALL NOT retain
problem labels in a hidden column or replacement table. Recovery backups MAY
preserve historical labels outside the migrated database.

The removal SHALL preserve every other current problem field and value,
learning row, foreign key and unrelated schema object. Existing legacy
provenance/difficulty upgrades remain governed by their existing requirements.
Problem manifests, patches, search and presentation SHALL continue to exclude
`topic_label`. The independent `flash_cards.topic_label` field and all its
existing values SHALL remain unchanged.

The explicitly authorized migration of registered course databases SHALL create
and prove recovery from an external SQLite backup before live deletion. The
observed c05 `problems_by_chapter` view SHALL omit only its `p.topic_label`
projection before the column drop, preserving its other SQL and columns.
Any other dependency on the target column SHALL block deletion and be reported.

#### Scenario: Open a current pool with historical problem labels

- **WHEN** schema ensure runs on a current pool with populated problem labels
- **THEN** `problems.topic_label` is absent from the resulting table
- **AND** all nontarget problem values, learning rows and flash-card labels are unchanged

#### Scenario: Rebuild a compatible legacy problem table

- **WHEN** schema ensure upgrades a compatible legacy problem table carrying labels
- **THEN** the rebuilt problem schema omits `topic_label`
- **AND** existing nontarget values and learning rows survive the upgrade

#### Scenario: Repeat schema ensure

- **WHEN** schema ensure runs again after removal
- **THEN** the problem label column is not reintroduced and no further schema change is reported

#### Scenario: Recover a database before live removal

- **WHEN** the operator prepares a registered course database for deletion
- **THEN** a separate SQLite backup and recovered copy prove that historical
  labels and all other data can be recovered before the live change

#### Scenario: A view references the retired column

- **WHEN** the registered c05 pool contains the observed `problems_by_chapter`
  view with a direct `p.topic_label` projection
- **THEN** the operator removes only that projection before dropping the column
- **AND** any additional dependency stops the migration for explicit review
