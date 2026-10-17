## ADDED Requirements

### Requirement: Paper execution state is consistent across reads and actions

Saved Paper reads SHALL distinguish its current container membership from any incompatible active or parked execution sharing its source identity. Backend reads SHALL expose consistent continuation availability and reasons based on the execution's ordered item identities, applicable revisions, item availability and current container validation. List and practice UIs SHALL follow that state and SHALL NOT present an incompatible execution's progress as the current Paper's progress or offer an enabled continuation action that is already known to be invalid. If another active saved Paper cannot be parked, a target Paper SHALL expose a separate start-block reason without replacing the target's own continuation status or progress. Start/continue writes SHALL independently validate the current state. After a rejected start, the list SHALL refresh the current count, progress, label and readiness in place while preserving local edits. Merely reading or rendering an incompatibility SHALL NOT discard or remap historical learning evidence.

#### Scenario: Container and execution have different items

- **WHEN** a saved Paper has 22 current items but its legacy execution has a different 70-item list
- **THEN** API and both UI entry points consistently report the incompatible execution and do not label 19/70 as progress on the 22-item Paper
- **AND** invalid continuation is not offered as enabled, while independently valid container management actions remain available

#### Scenario: Matching totals do not establish identity

- **WHEN** container and execution have the same count but different ordered item identities
- **THEN** they are still reported as incompatible without modifying either

#### Scenario: An unparkable active Paper blocks another Paper start

- **WHEN** an active saved Paper cannot continue or park, and another Paper has its own valid parked execution
- **THEN** the target keeps its own progress and reports that the active Paper blocks starting it
- **AND** the start action is rejected without changing either execution or learning evidence, while valid target management actions remain available

#### Scenario: Current manifest validation fails

- **WHEN** an active execution still matches its saved item identities but the current saved manifest fails validation
- **THEN** saved reads and the active-practice API report continuation as unavailable with a clear reason
- **AND** the practice UI does not offer that execution as resumable

#### Scenario: Valid execution and stale action

- **WHEN** the execution matches the current Paper and all required items are available
- **THEN** API and UI report the same progress and allow continuation
- **AND** a later content or structure change is revalidated on the action, with stale writes rejected and the UI refreshed truthfully
- **AND** the list updates its current count, progress, label and readiness without replacing local edits

#### Scenario: Missing item identifiers remain folded

- **WHEN** an incompatible execution references unavailable items
- **THEN** the reason is shown directly and the item identifiers remain inside collapsed details in the list or practice resume card
