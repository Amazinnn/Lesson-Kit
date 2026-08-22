## ADDED Requirements

### Requirement: Stable problem identity alongside figures

Problems SHALL expose a concise display title and a single topic label independently of their durable identifier. When a problem body contains a Markdown figure reference, adding those presentation fields SHALL NOT alter the figure path or its rendering in the workbench or Obsidian.

#### Scenario: A titled problem retains its figure

- **WHEN** a problem receives a display title and topic label
- **THEN** its existing Markdown figure reference resolves to the same logical figure path
