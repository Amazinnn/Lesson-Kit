## ADDED Requirements

### Requirement: Managed Paper Artifact actions resolve to saved Paper records

The Bridge SHALL accept a `paper_artifact` presentation action only after a successful `lesson-kit papers <workspace> save --input <manifest>` invocation has returned exit code 0 and a JSON receipt. The action SHALL identify a syntactically valid `ps-NNN` Paper in the selected workspace, and the Bridge SHALL resolve it against that workspace's existing managed Paper record. The normalized action's identity, title, and item count SHALL come from that record; model-supplied title or count SHALL NOT override it. An optional summary SHALL be limited to 300 characters and treated as presentation text, not proof of a save. A model-provided URL SHALL be discarded, and the normalized action SHALL contain no navigation URL. An invalid id or missing managed record SHALL produce no Artifact action and SHALL NOT write learning or Paper data.

#### Scenario: Emit a saved Paper Artifact

- **WHEN** a successful save receipt identifies a Paper that exists in the selected workspace's managed Paper store
- **THEN** the normalized `paper_artifact` action contains the managed record's id, title, and item count, plus the optional summary, and contains no URL

#### Scenario: Ignore model-only identity claims

- **WHEN** the action supplies a title or item count that differs from the matching managed Paper record
- **THEN** the normalized action uses the managed record's title and item count

#### Scenario: Reject an unmanaged or malformed Paper id

- **WHEN** the action id is malformed or no matching managed Paper record exists in the selected workspace
- **THEN** no Paper Artifact action is returned and no record is created

#### Scenario: Do not treat an export as a saved Paper

- **WHEN** the learner requested only a `pull --plan` manifest or `pull --print` sheet and no successful managed save receipt exists
- **THEN** the Bridge emits no Paper Artifact action

#### Scenario: Discard a model-provided destination

- **WHEN** a `paper_artifact` block includes a URL
- **THEN** the URL is removed from the normalized action and cannot control navigation
