## Purpose

Knowledge points with figures need a storage and display path that works in
both the web workbench and Obsidian: figures are files referenced by Markdown,
attached to knowledge points, and served statically.

## ADDED Requirements

### Requirement: Figures attached to knowledge points

A knowledge point SHALL support a list of figure file paths relative to the
workspace, stored on the knowledge point record. Adding or updating figure
references SHALL NOT require any change to existing knowledge point data.

#### Scenario: Attach a figure to a knowledge point

- **WHEN** the extraction pipeline records a figure file for a knowledge point
- **THEN** the figure path is stored on the knowledge point and the file remains at its workspace-relative location

### Requirement: Markdown figure references

Knowledge point body text SHALL reference figures with standard Markdown image
syntax, so the same source renders in the web workbench and in Obsidian without
a custom renderer.

#### Scenario: Figure renders in both surfaces

- **WHEN** a knowledge point body contains a Markdown image reference
- **THEN** the web workbench renders the image and the same Markdown file displays the image when opened as a document in Obsidian

### Requirement: Static figure serving

The web workbench SHALL serve figure files at a deterministic path derived from
the workspace name and the figure's relative location, and SHALL return a clear
error for missing files.

#### Scenario: Request a stored figure

- **WHEN** the browser requests a figure path for a stored figure
- **THEN** the file content is returned with an image content type

#### Scenario: Request a missing figure

- **WHEN** the browser requests a figure path that does not exist
- **THEN** a not-found response is returned and the UI shows a placeholder instead of a broken layout

### Requirement: Figures produced by extraction

The extraction pipeline SHALL land figure files (source screenshots or
re-drawings) into the workspace figure area during extraction, so figures exist
before views consume them. Figure asset management tooling is explicitly out of
scope for v1.

#### Scenario: Extraction writes a figure

- **WHEN** the extraction pipeline encounters a diagram that must be preserved for a knowledge point
- **THEN** it writes the figure file into the workspace figure area and records the reference on the knowledge point
