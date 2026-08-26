## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Safe superscript and subscript rendering

Learning content SHALL be escaped before rendering and SHALL promote only balanced, non-empty `<sup>` and `<sub>` pairs whose contents remain escaped. Unknown raw HTML, malformed tags, and unsafe attributes SHALL render as escaped text or be rejected before formal ingestion.

#### Scenario: Render a valid exponent

- **WHEN** gated learning content contains a balanced non-empty superscript
- **THEN** the exponent is rendered semantically without enabling arbitrary HTML

#### Scenario: Do not trust unknown HTML

- **WHEN** learning content contains an unsupported raw HTML element
- **THEN** the element is not executed or trusted as display markup

### Requirement: Component-aware graph presentation

The complete graph SHALL identify connected components, lay them out independently, arrange isolates outside dense connected regions, and pack the resulting components into the available canvas. Each nontrivial component SHALL choose deterministically among six initial layouts using edge crossings, label collisions, and spatial waste in that order. Remaining close edges MAY use shallow curves while preserving their semantic endpoints.

#### Scenario: Separate disconnected components

- **WHEN** a chapter graph has multiple connected components and isolated nodes
- **THEN** each component occupies a readable packed region and isolates do not collapse into the center of the largest component

#### Scenario: Choose a deterministic readable start

- **WHEN** the same component and viewport are laid out repeatedly
- **THEN** the same candidate wins the lexicographic crossing, collision, and waste comparison

#### Scenario: Respect reduced motion

- **WHEN** reduced motion is requested
- **THEN** the best stable component layouts are computed and drawn once without progressive animation

### Requirement: Neighborhood focus preserves graph context

Selecting a graph node SHALL fully emphasize the node and its one-hop neighbors, secondarily emphasize two-hop neighbors, and fade farther nodes with unrelated edges. Selecting the background SHALL restore the full graph.

#### Scenario: Focus a node neighborhood

- **WHEN** the learner selects a node
- **THEN** one-hop, two-hop, and farther graph elements receive the defined emphasis levels without removing topology

#### Scenario: Reset graph focus

- **WHEN** the learner selects the graph background
- **THEN** all nodes and edges return to the complete-graph presentation
