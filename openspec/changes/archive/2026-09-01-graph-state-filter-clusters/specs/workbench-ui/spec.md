## ADDED Requirements

### Requirement: Multi-state graph filtering

The knowledge graph SHALL expose a multi-select learning-state filter using exactly `needs_work`, `review`, `mastered`, and `null` as its values. No selected value SHALL mean no filtering. One or more selected values SHALL retain the union of matching nodes and only edges whose two endpoints remain visible. Filtering SHALL be independent of the active graph projection and SHALL NOT change the explicit practice selection or any learning data.

#### Scenario: Show one state

- **WHEN** the learner selects only `review`
- **THEN** review nodes remain visible and all nonmatching nodes and incident edges fade out before leaving the active layout

#### Scenario: Show several states

- **WHEN** the learner selects `needs_work` and `mastered`
- **THEN** nodes from both categories and edges between visible endpoints remain in the graph

#### Scenario: Clear filtering

- **WHEN** the learner clears every selected state
- **THEN** all nodes and relationships reappear without changing the practice selection

### Requirement: State cluster layout

When state filtering is active, each visible state SHALL receive a deterministic cluster center. Nodes SHALL move through the existing bounded-velocity force simulation toward their state's center, so one selected category forms one group and multiple selected categories form separate groups. Cross-category edges MAY remain visible but SHALL exert reduced pull so the groups stay distinguishable. Reduced-motion mode SHALL draw the stable filtered layout without transition frames.

#### Scenario: One selected category forms one group

- **WHEN** exactly one state is selected
- **THEN** its visible nodes gather around one central cluster target

#### Scenario: Several selected categories form separate groups

- **WHEN** two or more states are selected
- **THEN** each state gathers around a separate deterministic center while visible relationships remain attached

#### Scenario: Reduced-motion filtering

- **WHEN** a reduced-motion learner changes the state filter
- **THEN** the graph draws the stable filtered clusters without scheduling fade or movement frames

