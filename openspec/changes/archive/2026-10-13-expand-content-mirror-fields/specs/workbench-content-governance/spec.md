## ADDED Requirements

### Requirement: Extended authored fields in the JSON content projection

The v1 JSON content projection SHALL include `figure_paths` for knowledge
points and durable problems, and the four objective difficulty dimensions,
derived total, and model for durable problems. These fields are optional in a
pool projection when their columns are unavailable; the mirror SHALL NOT create
columns to complete a projection. `figure_paths` SHALL remain logical references
only. JSON mirror synchronization SHALL NOT create, copy, rename, or transport
figure bytes, and SHALL NOT resolve the repository-wide figure naming policy.

Before classifying or applying a synchronization plan, every present figure
reference on either side SHALL be a non-empty string accepted by the existing
course-relative logical figure path rules. A rejected reference SHALL make the
entity invalid before any pool, JSON, mirror-state, or mirror-log write. Binary
figure synchronization remains a separate explicit operation.

The four objective difficulty dimensions SHALL be either all null or all
present. A non-null replacement rating SHALL be explicit only when at least one
of its four incoming dimension values differs from the synchronized baseline;
the complete vector SHALL be validated and the derived total and model SHALL be
recomputed through the existing difficulty validation authority. Unchanged
dimension values MAY be carried when at least one other dimension changes. A
complete vector carried unchanged alongside a content-axis edit SHALL NOT
count as a replacement and the stale rating SHALL be cleared. An all-null
group SHALL continue to clear the rating. Direct edits to the derived fields
alone SHALL be invalid. A content-axis edit that invalidates a stored rating
SHALL clear only difficulty fields represented by the current pool projection.
An explicit replacement rating SHALL be invalid during check if the pool
schema does not expose the complete difficulty group. No schema migration or
inferred dimension value is permitted.

#### Scenario: Repository figure references round-trip for both owner types

- **GIVEN** a tracked knowledge point or durable problem has a valid logical figure path
- **WHEN** its next repository revision changes `figure_paths` to another valid array
- **THEN** check accepts the reference and sync stores that JSON array in the matching pool owner
- **AND** no figure file or binary index is created or changed by JSON mirror sync

#### Scenario: Invalid figure references are rejected before writes

- **GIVEN** a repository revision contains a non-string, empty, traversal, cross-course, or unsupported-extension figure path
- **WHEN** check or sync plans the entity
- **THEN** the entity is invalid and the pool row, repository JSON, mirror state, and mirror log remain unchanged

#### Scenario: A changed complete difficulty vector determines derived values

- **GIVEN** the pool exposes the complete difficulty group and a repository revision supplies all four non-null dimensions with at least one value changed from the synchronized baseline
- **WHEN** check and sync process that revision
- **THEN** the complete vector is validated, the total and model are recomputed, and the normalized group is stored
- **AND** unchanged dimension values in that vector are allowed
- **AND** a revision that changes only the derived total or model is invalid

#### Scenario: Content edits clear only available difficulty fields

- **GIVEN** a problem's pool schema exposes none or only part of the difficulty group
- **AND** a repository revision changes a content-axis field such as `problem_text`
- **WHEN** check and sync process that revision
- **THEN** both classify the same valid content update, sync clears only difficulty columns present in the projection, and no column is added
- **AND** an explicit replacement rating against an incomplete group is invalid during check

#### Scenario: A carried-over vector does not replace a stale rating

- **GIVEN** a problem has a complete difficulty vector in its synchronized baseline
- **AND** a JSON revision changes a content-axis field but carries all four baseline dimensions unchanged
- **WHEN** check and sync process that revision
- **THEN** the carried-over vector is not a replacement rating, stale difficulty fields represented by the pool projection are cleared, and no value is inferred

### Requirement: Additive v1 projection upgrades preserve revision safety

Adding the approved fields SHALL be an additive projection upgrade within JSON
`schema_version` 1. An older v1 file and mirror baseline MAY omit fields that
were not in the earlier projection. When an incoming full projection at exactly
the expected next revision normalizes to the current pool projection, the
mirror SHALL allow the older workspace to adopt that revision once and record
the full baseline. Read-only commands SHALL remain zero-write. An unchanged
repository projection with a mismatched revision SHALL be invalid unless it
meets this exact projection-upgrade convergence case; changed payloads SHALL
continue to follow the one-step revision and conflict rules.

#### Scenario: A second workspace adopts the first workspace's projection upgrade

- **GIVEN** a workspace has an older v1 baseline at revision 1
- **AND** the repository contains the complete current projection at revision 2 matching that workspace's pool
- **WHEN** check runs and then sync is applied
- **THEN** check writes nothing, sync records the complete revision-2 baseline once, and the next sync is a no-op

#### Scenario: Revision spoofing and divergent edits remain rejected

- **GIVEN** a repository revision is unchanged despite an upgrade, skips the expected next revision, or differs from a changed pool projection
- **WHEN** check or sync evaluates the entity
- **THEN** the unchanged-revision or wrong-revision payload is invalid, and divergent pool and repository edits remain a conflict with no entity writes
