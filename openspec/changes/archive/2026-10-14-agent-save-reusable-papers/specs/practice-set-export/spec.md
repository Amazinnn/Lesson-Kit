## ADDED Requirements

### Requirement: Agent can explicitly save a reusable paper
The system SHALL expose `lesson-kit papers <workspace> save --input <manifest>` to save an existing practice-set manifest using the same managed store as the browser. It SHALL preserve the ordered problem IDs and request metadata, validate the manifest before saving, and reject a supplied course that differs from the selected workspace course. It SHALL leave SQLite, learning state, the source manifest and existing saved papers unchanged.

#### Scenario: Save a valid composed paper
- **WHEN** the caller saves a valid manifest containing existing unique ordered problem IDs
- **THEN** the command exits 0 and returns JSON containing the persisted `practice_set_id`, title, count and workspace-relative group-paper page URL
- **AND** the saved paper is readable through the existing browser paper list and retains the same problem order and request metadata

#### Scenario: Reject an invalid or cross-course manifest
- **WHEN** the input is unreadable or malformed, violates the existing practice-set manifest contract, references unknown or duplicate IDs, lacks a valid title/request, or declares a different course
- **THEN** the command exits 2 with a JSON error and creates no saved paper or database changes

### Requirement: Agent distinguishes exported and managed papers
The Agent practice contract SHALL distinguish `pull --plan`/`--print` exports from managed saved papers. When the learner requests saving a paper or making it available in Workbench, the contract SHALL direct the Agent to the managed-save command and require a successful receipt before reporting success. Export-only requests SHALL remain supported.

#### Scenario: Report a successful managed save
- **WHEN** managed saving succeeds
- **THEN** the Agent can report the saved title, count and returned page link without representing a job artifact as the saved paper

#### Scenario: Export alone does not prove saving
- **WHEN** only a job manifest or printed sheet exists, or managed saving fails
- **THEN** the contract prohibits claiming that the paper is saved in the Workbench list
