## Purpose

Knowledge points and problems with figures need a declared, first-class figure
area: figures are files under the workspace's hidden runtime directory,
referenced by logical paths in the pool and by Markdown in text, served by the
web workbench and rendered by Obsidian.

## ADDED Requirements

### Requirement: Declared figure area

The figure area SHALL be the workspace's `.lessonkit/figures/{course}/{chapter}/`
directory, following the project convention that runtime files live in hidden
dot-directories. Figure files SHALL be named `{owner_id}-fig-{NNN}.png` where
the owner is a knowledge point or problem id. The pool SHALL store only logical
paths (`{course}/{chapter}/{owner_id}-fig-{NNN}.png`), and each display surface
resolves them itself.

#### Scenario: A knowledge point figure is stored in the figure area

- **WHEN** the extraction pipeline lands a figure for a knowledge point
- **THEN** the file is written to `.lessonkit/figures/{course}/{chapter}/{kp_id}-fig-001.png` and the logical path is stored on the knowledge point

### Requirement: Figures attached to knowledge points and problems

A knowledge point or a durable problem SHALL support a list of figure logical
paths stored on its record. Problem figures exist so that diagrams which are
part of the question itself (Karnaugh maps, circuit diagrams, force diagrams)
render inside the problem statement. Adding or updating figure references
SHALL NOT require changes to existing data.

#### Scenario: A problem embeds its diagram

- **WHEN** a problem's figure is part of its statement (a Karnaugh map problem)
- **THEN** the problem record lists the figure path and the practice page renders the figure inside the problem statement

### Requirement: Markdown figure references

Knowledge point and problem text SHALL reference figures with standard Markdown
image syntax, so the same source renders in the web workbench and in Obsidian
without a custom renderer. Rendering of figures inside the hidden dot-directory
in Obsidian SHALL be verified during implementation; if a viewer excludes
hidden directories, the exclusion is treated as a known limitation with a
documented workaround, not a v1 blocker.

#### Scenario: Figure renders in both surfaces

- **WHEN** text contains a Markdown image reference to a figure in the figure area
- **THEN** the web workbench renders the image, and the same Markdown displays the image when opened in Obsidian (or, if Obsidian hides dot-directories, the documented workaround is applied)

### Requirement: Static figure serving

The web workbench SHALL serve figure files at a deterministic path derived from
the workspace name and the figure's logical path, with path-traversal
protection, and SHALL return a clear error for missing files.

#### Scenario: Request a stored figure

- **WHEN** the browser requests a figure path for a stored figure
- **THEN** the file content is returned with an image content type

#### Scenario: Request a missing figure

- **WHEN** the browser requests a figure path that does not exist
- **THEN** a not-found response is returned and the UI shows a placeholder instead of a broken layout

### Requirement: Figures produced by extraction

The extraction pipeline SHALL land figure files — knowledge-point figures and
problem-embedded figures — into the figure area during extraction, so figures
exist before views consume them. Figure asset management tooling is explicitly
out of scope for v1.

#### Scenario: Extraction writes a figure

- **WHEN** the extraction pipeline encounters a diagram that must be preserved for a knowledge point or a problem
- **THEN** it writes the figure file into the figure area and records the logical reference on the owner record
