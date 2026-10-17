## ADDED Requirements

### Requirement: Paper execution state is consistent across reads and actions

Saved Paper reads SHALL distinguish its current container membership from any incompatible active or parked execution sharing its source identity. Backend reads SHALL expose consistent continuation availability and reasons based on the execution's ordered item identities, applicable revisions and item availability. List and practice UIs SHALL follow that state and SHALL NOT present an incompatible execution's progress as the current Paper's progress or offer an enabled continuation action that is already known to be invalid. Start/continue writes SHALL independently validate the current state. Merely reading or rendering an incompatibility SHALL NOT discard or remap historical learning evidence.

#### Scenario: Container and execution have different items

- **WHEN** a saved Paper has 22 current items but its legacy execution has a different 70-item list
- **THEN** API and both UI entry points consistently report the incompatible execution and do not label 19/70 as progress on the 22-item Paper
- **AND** invalid continuation is not offered as enabled, while independently valid container management actions remain available

#### Scenario: Matching totals do not establish identity

- **WHEN** container and execution have the same count but different ordered item identities
- **THEN** they are still reported as incompatible without modifying either

#### Scenario: Valid execution and stale action

- **WHEN** the execution matches the current Paper and all required items are available
- **THEN** API and UI report the same progress and allow continuation
- **AND** a later content or structure change is revalidated on the action, with stale writes rejected and the UI refreshed truthfully
