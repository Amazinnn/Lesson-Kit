## ADDED Requirements

### Requirement: Cross-page practice-scope tray

Every workspace page SHALL expose one compact practice-scope control at the
upper-right of the middle column. Activating it SHALL open a tray that lists
the complete names of the knowledge points in the current explicit selection,
allows an item to be removed, and offers one action to enter practice with the
remaining selection. The list SHALL scroll vertically inside a bounded panel
when it grows, and a minus control SHALL collapse the tray back to the compact
button. Selection and open/collapsed state SHALL remain in sync while the
learner navigates workspace pages in the same tab. The tray SHALL reuse the
existing tab-local selection and SHALL NOT create server-side state.

#### Scenario: Inspect a long selection

- **WHEN** the learner opens the tray with more selected knowledge points than
  fit in its bounded list area
- **THEN** every selected name remains available through vertical scrolling
  inside the tray without expanding the page header

#### Scenario: Remove a selected point from the tray

- **WHEN** the learner removes one knowledge point in the tray
- **THEN** it disappears from the tray and is deselected in the knowledge list,
  graph, and staged practice list through the existing selection state

#### Scenario: Collapse and navigate

- **WHEN** the learner collapses the tray with the minus control and navigates
  to another page in the same workspace tab
- **THEN** the compact button remains visible, the tray remains collapsed, and
  the selected knowledge points are unchanged

#### Scenario: Start practice from the tray

- **WHEN** at least one knowledge point is selected and the learner activates
  the tray's practice action
- **THEN** the practice page opens with that same explicit selection
