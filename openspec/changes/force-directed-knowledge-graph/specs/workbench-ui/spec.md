## MODIFIED Requirements

### Requirement: Knowledge graph page

The knowledge graph page SHALL render the current chapter graph from live workspace data inside the workbench rather than embedding a generated artifact. The middle column SHALL provide graph search, state filtering, zoom, pan, drag, fit, and focus. Nodes SHALL be circular with external readable labels; current state SHALL control color and the formal-problem count SHALL control radius. Connected nodes SHALL be positioned by a force simulation in which stronger semantic edges have shorter target distances. The outer right column SHALL switch between knowledge-point detail and the existing AI teacher panel; the graph SHALL NOT render its own nested side columns or scroll containers. Graph coordinates and navigation gestures SHALL NOT be persisted as learning records or interaction logs.

#### Scenario: See a current graph state

- **WHEN** a learner changes a knowledge-point state and refreshes the graph
- **THEN** the changed state is rendered from the workspace data

#### Scenario: Read coverage and closeness

- **WHEN** the graph contains nodes with different formal-problem counts and connected edges of different attraction
- **THEN** nodes with more formal problems are larger and stronger connected pairs settle at shorter target distances

#### Scenario: Navigate the graph directly

- **WHEN** the learner drags a node, pans the background, zooms, or fits the graph
- **THEN** the native canvas updates in memory and focused knowledge-point detail remains available in the outer right column

#### Scenario: Filter the visible graph

- **WHEN** the learner searches or filters by learning state
- **THEN** the remaining nodes are re-laid out and the simulation reheats without restoring removed nodes' coordinates as durable state

#### Scenario: Prefer reduced motion

- **WHEN** the browser reports `prefers-reduced-motion: reduce`
- **THEN** the graph computes a stable layout without progressive animation and paints the result once

#### Scenario: Inspect a focused node

- **WHEN** the learner focuses a graph node
- **THEN** the outer right detail tab presents its readable title, current state, related knowledge points, and safe editable fields

#### Scenario: Open the knowledge graph

- **WHEN** the learner clicks the knowledge graph navigation entry
- **THEN** the middle area displays the current chapter graph from the workspace data

#### Scenario: Graph artifact missing

- **WHEN** no rendered graph artifact exists on disk
- **THEN** the graph page remains available because it uses workspace data rather than the artifact
