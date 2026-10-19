## REMOVED Requirements

### Requirement: Practice page suggestions and assembly entry
**Reason**: All learner-operated assembly controls are retired, including scope summaries and suggestion-to-assembly actions.
**Migration**: Agent/CLI authors Papers; the page manages and practises existing Papers. Preserve read-only study suggestions where they do not select or assemble questions.

### Requirement: Cross-page practice-scope tray
**Reason**: The learner no longer collects an assembly scope through page controls.
**Migration**: Remove tray, selection badges, add/remove scope actions and assembly navigation. Preserve ordinary reading, graph focus and Agent context without implicit selection.

## MODIFIED Requirements

### Requirement: Practice page

The practice page SHALL list/manage existing Papers and offer start/continue, not learner-operated selection or assembly. It SHALL NOT expose per-problem pickers, knowledge-point assembly selectors, quantity/source/difficulty assembly controls, content-mode assembly inputs, suggestion-to-assembly actions, manual Paper membership/order edits, or a scope tray. Agent/CLI Paper Assembly and saving SHALL remain available. Reading, graph navigation and chapter-lens changes SHALL NOT select or assemble practice items. Existing Paper progress SHALL remain independent of these reading actions.

#### Scenario: Start from an explicit scope
- **WHEN** the learner asks the Agent to assemble from an explicit knowledge scope
- **THEN** the Agent authors/saves the fixed Paper and the page offers that saved Paper for practice without a learner scope-selection form

#### Scenario: Resume an active Paper
- **WHEN** the learner returns with an unfinished run
- **THEN** its Paper and progress are offered for continuation without assembly

#### Scenario: Filters do not mutate a running Paper
- **WHEN** Agent/CLI authoring filters or reading context change
- **THEN** the running Paper remains fixed and any authoring inputs apply only to a separately authored Paper

#### Scenario: No manual problem picker
- **WHEN** the learner visits practice, knowledge points, graph or saved-Paper surfaces
- **THEN** no learner action selects concrete questions, accumulates assembly scope, changes a Paper's item list/order or directly assembles a Paper

### Requirement: Saved paper items preview their problem

The saved-Paper page SHALL allow reading each item's full text and source in a collapsed-by-default expandable block using the shared safe Markdown subset, including math, figures and code. Summaries SHALL show index and title without reorder/remove controls. Preview SHALL change no Paper or practice state.

#### Scenario: Read one problem of a saved paper
- **WHEN** an item is expanded
- **THEN** its text and recorded source appear without leaving the page

#### Scenario: A long paper stays scannable
- **WHEN** a Paper contains many items
- **THEN** items arrive collapsed with visible disclosure controls

#### Scenario: Preview does not disturb the paper
- **WHEN** items are expanded or collapsed
- **THEN** membership, order and execution state remain unchanged, and no learner reorder/remove controls appear

### Requirement: Saved paper cards fold

Saved Paper cards SHALL arrive folded with title, count and management controls visible. Learners SHALL retain preview, rename, export, container deletion and start/continue as applicable, without membership/order editing. Fold state SHALL be reading-only, persist within the tab across management refreshes, and not change because a head control is activated. Errors SHALL remain visible on folded cards.

#### Scenario: A folded card shows its head only
- **WHEN** the saved-Paper page renders
- **THEN** title, count and management controls remain visible while items fold away

#### Scenario: An edit leaves the paper open
- **WHEN** a learner renames an open Paper and its management view refreshes
- **THEN** the card remains open in that tab

#### Scenario: A control does not fold the card
- **WHEN** rename or start/continue is activated
- **THEN** the action runs without toggling the card

#### Scenario: An error remains visible on a folded card
- **WHEN** rename or export fails on a folded card
- **THEN** its readable error remains visible outside the item list
