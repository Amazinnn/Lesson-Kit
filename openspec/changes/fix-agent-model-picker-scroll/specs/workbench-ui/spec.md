## ADDED Requirements

### Requirement: Long provider lists remain navigable
At desktop widths, when the visible new-conversation provider picker has more model options than fit in the available height, the system SHALL allow the learner to scroll the options with native wheel input while keeping the picker heading and helper text visible.

#### Scenario: Scroll a long provider list
- **WHEN** the learner opens the provider picker with a long model list and wheels up or down over the options at desktop width
- **THEN** the options move in the requested direction while the picker heading and helper text remain visible
