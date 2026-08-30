## MODIFIED Requirements

### Requirement: Explicit content mutation boundary

Pool content SHALL change only after an explicit create, update, delete, or
state command, or through the structured check ingest action defined by the
ai-teacher-bridge capability. Browsing, search, navigation, draft text,
ordinary Agent conversation, and provider tool events SHALL NOT mutate pool or
learning data. After a successful Agent mutation, the teacher answer SHALL expose a concise object, action, and workbench-link summary rather than raw commands, SQL, or tool logs.

#### Scenario: Discuss a possible edit

- **WHEN** the learner discusses changing a knowledge point without explicitly asking to apply the change
- **THEN** the Agent may explain or propose the edit but no data command is issued

#### Scenario: Apply an explicit edit

- **WHEN** the learner explicitly requests a content change and the Agent completes it
- **THEN** the answer identifies the changed object and action with a workbench link and omits internal command logs

#### Scenario: Apply content through the bridge check action

- **WHEN** the learner explicitly asks in an Agent conversation to add pool content and the reply carries a valid check ingest action
- **THEN** the pool changes only through the same deterministic gate and batch-recorded apply as the CLI recipes
