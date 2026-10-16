## ADDED Requirements

### Requirement: Managed Paper Artifact actions resolve to saved Paper records

The on-demand `actions` contract SHALL instruct the Agent to emit a `paper_artifact` presentation action only after it has run `lesson-kit papers <workspace> save --input <manifest>` and observed exit code 0 with a JSON receipt. For a received action, the Workbench SHALL validate a syntactically valid `ps-NNN` id in the selected workspace and resolve it against that workspace's existing managed Paper record. The normalized action's identity, title, and item count SHALL come from that record; model-supplied title or count SHALL NOT override it. The action block is not a receipt ledger and does not by itself prove which command produced the id. An optional summary SHALL be limited to 300 characters and treated as presentation text, not proof of a save. A model-provided URL SHALL be discarded, and the normalized action SHALL contain no navigation URL. An invalid id or missing managed record SHALL produce no Artifact action and SHALL NOT write learning or Paper data.

#### Scenario: Agent follows the managed-save instruction

- **WHEN** the Agent receives exit code 0 and a JSON receipt from the managed Paper save command
- **THEN** its action contract directs it to emit `paper_artifact` with the Paper id from that receipt and no navigation URL

#### Scenario: Resolve the selected workspace record

- **WHEN** the Workbench receives a syntactically valid Paper id with a matching record in the selected workspace
- **THEN** the normalized action contains the managed record's id, title, and item count, plus the optional summary, and contains no URL

#### Scenario: Ignore model-only identity claims

- **WHEN** the action supplies a title or item count that differs from the matching managed Paper record
- **THEN** the normalized action uses the managed record's title and item count

#### Scenario: Reject an unmanaged or malformed Paper id

- **WHEN** the action id is malformed or no matching managed Paper record exists in the selected workspace
- **THEN** no Paper Artifact action is returned and no record is created

#### Scenario: Do not treat an export as a saved Paper

- **WHEN** the learner requested only a `pull --plan` manifest or `pull --print` sheet and no successful managed save receipt exists
- **THEN** the Agent's action contract directs it to emit no Paper Artifact action

#### Scenario: Discard a model-provided destination

- **WHEN** a `paper_artifact` block includes a URL
- **THEN** the URL is removed from the normalized action and cannot control navigation
