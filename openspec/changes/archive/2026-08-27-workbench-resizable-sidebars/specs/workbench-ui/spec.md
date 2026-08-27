## ADDED Requirements

### Requirement: Resizable desktop sidebars

The desktop workbench SHALL expose pointer-drag handles on the inner edges of the left and right columns. Dragging SHALL adjust only the current page's in-memory grid widths within readable bounds; mobile drawer behavior and all learning data SHALL remain unchanged.

#### Scenario: Resize sidebars

- **WHEN** the learner drags a sidebar edge on a desktop viewport
- **THEN** the corresponding column width changes within its bounds without navigation or persistence

### Requirement: Scrollable Agent conversation

The Agent chat SHALL constrain its message region to the available column height and allow normal mouse-wheel vertical scrolling when messages exceed that height.

#### Scenario: Read long conversation

- **WHEN** the Agent message list is taller than the visible right column
- **THEN** the learner can scroll the message region with the mouse wheel while the input remains available
