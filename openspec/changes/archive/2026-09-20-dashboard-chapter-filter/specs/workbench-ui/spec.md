## MODIFIED Requirements

### Requirement: Three-column shell with navigation

The workbench SHALL render a three-column desktop layout: a left navigation column with workspace and study navigation, a primary middle page, and a collapsible right Agent conversation column, with the workspace name and the chapter lens in the top bar (the machine course identifier SHALL NOT be shown there). At narrow widths the middle page SHALL remain the single primary column; the left and right columns SHALL become dismissible drawers opened by two compact icon controls in the top bar. Switching workspaces or pages SHALL preserve recorded pool state.

#### Scenario: Navigate from the left column

- **WHEN** the learner clicks a navigation entry in the left column
- **THEN** the middle area shows the corresponding page for the current workspace

#### Scenario: Open mobile navigation

- **WHEN** a learner at a narrow viewport activates the navigation icon
- **THEN** the left column opens as a drawer without hiding the middle page permanently

#### Scenario: Open mobile Agent conversation

- **WHEN** a learner at a narrow viewport activates the conversation icon
- **THEN** the right column opens as a drawer and can be dismissed back to the middle page

#### Scenario: Switch workspace without losing state

- **WHEN** the learner switches the workspace dropdown
- **THEN** the new workspace loads and previously recorded attempts, feedback, and signals remain intact in their original pool

#### Scenario: The top bar shows the name, not the identifier

- **WHEN** a workspace's course is an automatically allocated code and its name is the folder name
- **THEN** the top bar shows the workspace name, and the code does not appear there

#### Scenario: The chapter context lives in the lens control

- **WHEN** a chapter is active
- **THEN** the top bar shows it through the chapter lens control rather than repeating it beside the workspace name

## ADDED Requirements

### Requirement: Chapter switch in the top bar

The workbench top bar SHALL carry one chapter control beside the workspace and
course context: a switch whose off state means the whole course and whose on
state selects exactly one chapter from the chapters present in the pool. The
control SHALL write the active chapter through the service and refresh the
shell, SHALL NOT introduce a fourth navigation page, and SHALL show no
per-chapter statistics, counts, or selection reasons.

#### Scenario: Toggle the lens on

- **WHEN** the learner turns the chapter switch on and selects a chapter
- **THEN** the shell reloads with that chapter's context and the control shows the selected chapter

#### Scenario: Toggle the lens off

- **WHEN** the learner turns the chapter switch off
- **THEN** the shell reloads with the whole-course context and the control shows no chapter

#### Scenario: No new navigation surface

- **WHEN** the chapter control is used
- **THEN** the three-page shell and its navigation entries remain unchanged
