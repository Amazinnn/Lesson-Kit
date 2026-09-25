## ADDED Requirements

### Requirement: Failed activities expose a concise error summary

A failed activity SHALL display a sanitized error summary of at most 240
characters without requiring expansion. Full bounded tool output SHALL remain
collapsed by default. Empty output SHALL produce an explicit generic failure
message. Existing sensitive-value redaction SHALL precede truncation/storage.

#### Scenario: Pi tool reports an error

- **WHEN** Pi emits tool_execution_end with isError=true and diagnostic text
- **THEN** the activity visibly shows failure and its short diagnostic while full output remains collapsed

#### Scenario: Error output is empty

- **WHEN** a tool fails without diagnostic text
- **THEN** the activity shows a generic failure summary rather than a blank detail

#### Scenario: Failure contains sensitive and long output

- **WHEN** a failed activity contains secrets and more than 240 characters
- **THEN** its summary is redacted and bounded and cannot expose the removed sensitive values
