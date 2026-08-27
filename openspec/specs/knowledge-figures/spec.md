## Purpose

Knowledge points and problems with figures need a declared, first-class figure
area: figures are files under the workspace's hidden runtime directory,
referenced by logical paths in the pool and by Markdown in text, served by the
web workbench and rendered by Obsidian.
## Requirements
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

### Requirement: Stable problem identity alongside figures

Problems SHALL expose a concise display title and a single topic label independently of their durable identifier. When a problem body contains a Markdown figure reference, adding those presentation fields SHALL NOT alter the figure path or its rendering in the workbench or Obsidian.

#### Scenario: A titled problem retains its figure

- **WHEN** a problem receives a display title and topic label
- **THEN** its existing Markdown figure reference resolves to the same logical figure path

### Requirement: Explicit graph content updates preserve learning history

The formal knowledge-point page SHALL own knowledge-point body and fragile-note editing. The graph SHALL provide a link to that page instead of duplicate content editors. Existing explicit compatibility operations MAY update those fields and SHALL NOT alter relations, problem content, feedback events, or learner signals.

#### Scenario: Open content editing from the graph

- **WHEN** a learner needs to read or edit a selected graph node's knowledge content
- **THEN** the graph links to the formal knowledge-point page and renders no duplicate body or fragile-note editor

#### Scenario: Compatibility update preserves learning history

- **WHEN** an existing explicit content-update operation saves a knowledge-point body or fragile note
- **THEN** relation, feedback-event, and learner-signal counts remain unchanged

#### Scenario: Saving a knowledge point does not create learning events

- **WHEN** a learner saves a knowledge point body or fragile note from its formal page or compatibility operation
- **THEN** the refreshed content shows the change while relation, feedback-event, and learner-signal counts remain unchanged

### Requirement: Safe superscript and subscript rendering

Learning content SHALL be escaped before rendering and SHALL promote only balanced, non-empty `<sup>` and `<sub>` pairs whose contents remain escaped. Unknown raw HTML, malformed tags, and unsafe attributes SHALL render as escaped text or be rejected before formal ingestion.

#### Scenario: Render a valid exponent

- **WHEN** gated learning content contains a balanced non-empty superscript
- **THEN** the exponent is rendered semantically without enabling arbitrary HTML

#### Scenario: Do not trust unknown HTML

- **WHEN** learning content contains an unsupported raw HTML element
- **THEN** the element is not executed or trusted as display markup

### Requirement: Component-aware graph presentation

The complete graph SHALL identify connected components and choose deterministic seed coordinates for each nontrivial component from six initial layouts using edge crossings, label collisions, and spatial waste in that order. Those packed seeds SHALL then enter one unified elastic field, while isolates retain separate initial regions. Stronger semantic edges SHALL have shorter targets than weaker edges, every pair of node circles SHALL retain at least 24 pixels of logical clearance, and labels SHALL NOT enlarge physical collision radii. Remaining obstructed edges SHALL use deterministic shallow curves while preserving their semantic endpoints.

#### Scenario: Separate disconnected components

- **WHEN** a chapter graph has multiple components and isolated nodes
- **THEN** deterministic component layouts provide readable initial regions before all visible nodes enter one runtime field

#### Scenario: Choose a deterministic readable start

- **WHEN** the same component and viewport are laid out repeatedly
- **THEN** the same candidate wins the lexicographic crossing, collision, and waste comparison

#### Scenario: Preserve semantic distance and clearance

- **WHEN** connected edges have different attraction and nodes have different radii
- **THEN** stronger edges have shorter center targets while every node pair retains the minimum circle clearance

#### Scenario: Respect reduced motion

- **WHEN** reduced motion is requested
- **THEN** the unified field computes a stable layout and is drawn once without progressive or idle animation

### Requirement: Neighborhood focus preserves graph context

Selecting a graph node SHALL fully emphasize and gently expand its one-hop neighborhood, secondarily emphasize and expand two-hop neighbors, and fade farther nodes with unrelated edges. Expansion SHALL preserve stronger-edge-before-weaker-edge distance ordering and SHALL NOT recenter the camera. Selecting the background SHALL restore the complete graph and ordinary semantic targets.

#### Scenario: Focus a node neighborhood

- **WHEN** the learner selects a node
- **THEN** one-hop and two-hop neighborhoods expand in place with their emphasis levels while farther topology remains present

#### Scenario: Reset graph focus

- **WHEN** the learner selects the graph background
- **THEN** all nodes and edges return to the complete-graph presentation and ordinary semantic targets
