## ADDED Requirements

### Requirement: Stable problem identity alongside figures

Problems SHALL expose a concise display title and a single topic label independently of their durable identifier. When a problem body contains a Markdown figure reference, adding those presentation fields SHALL NOT alter the figure path or its rendering in the workbench or Obsidian.

#### Scenario: A titled problem retains its figure

- **WHEN** a problem receives a display title and topic label
- **THEN** its existing Markdown figure reference resolves to the same logical figure path

### Requirement: Explicit graph content updates preserve learning history

The workbench graph SHALL allow an explicit save of a knowledge point body and fragile note. It SHALL update only those fields and SHALL NOT alter relations, problem content, feedback events, or learner signals.

#### Scenario: Saving a knowledge point does not create learning events

- **WHEN** a learner saves a knowledge point body and fragile note from the graph
- **THEN** the refreshed graph model shows the new content while relation, feedback-event, and learner-signal counts are unchanged
