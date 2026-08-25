# workbench-content-governance Specification

## Purpose
TBD - created by archiving change agent-native-workbench-conversation. Update Purpose after archive.
## Requirements
### Requirement: Explicit content mutation boundary

Pool content SHALL change only after an explicit create, update, delete, state, gate, or promote command. Browsing, search, navigation, draft text, ordinary Agent conversation, and provider tool events SHALL NOT mutate pool or learning data. After a successful Agent mutation, the teacher answer SHALL expose a concise object, action, and workbench-link summary rather than raw commands, SQL, or tool logs.

#### Scenario: Discuss a possible edit

- **WHEN** the learner discusses changing a knowledge point without explicitly asking to apply the change
- **THEN** the Agent may explain or propose the edit but no data command is issued

#### Scenario: Apply an explicit edit

- **WHEN** the learner explicitly requests a content change and the Agent completes it
- **THEN** the answer identifies the changed object and action with a workbench link and omits internal command logs

### Requirement: Transactional physical deletion

Content deletion SHALL be physical and atomic, with no tombstone or deletion log. Deleting a problem SHALL remove its current state, schedule, signals, attempts, progress, and feedback. Deleting a knowledge point SHALL remove its relations and membership from multi-owned problems, and SHALL delete any newly ownerless problem with the same cascade. Deleting a relation SHALL remove only that relation.

#### Scenario: Delete a problem with learning records

- **WHEN** a formal problem is explicitly deleted
- **THEN** the problem and every dependent learning row are absent after one committed transaction

#### Scenario: Delete a knowledge point with shared and ownerless problems

- **WHEN** a knowledge point owns both a shared problem and a sole-owned problem
- **THEN** the shared problem remains without that membership, the sole-owned problem and its dependent rows are deleted, and all attached relations are removed atomically

#### Scenario: A deletion step fails

- **WHEN** any statement in a content deletion transaction fails
- **THEN** the entire deletion is rolled back and the original content remains

### Requirement: Current-state replacement without event noise

An explicit `state` command SHALL replace the current knowledge-point or problem state and update its schedule through the existing equivalent rating. It SHALL NOT append a feedback event, learner signal, or conversation-side learning log.

#### Scenario: Replace state through Agent data

- **WHEN** the Agent explicitly sets an item to `mastered`
- **THEN** current state and schedule reflect rating 5 while feedback and signal counts remain unchanged

