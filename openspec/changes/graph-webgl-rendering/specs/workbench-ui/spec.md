## MODIFIED Requirements

### Requirement: Knowledge graph page

When browser Web Worker support, graph physics resources, and WebGL2 support are available, the knowledge graph page SHALL render the live complete chapter graph in a middle-column canvas that fills the viewport below its compact page tools. Six deterministic component layouts SHALL supply seed positions before every visible node enters one unbounded unified elastic field. Existing edge attraction SHALL determine variable semantic gaps from 72 to 144 pixels in addition to endpoint radii, and every pair of node circles SHALL retain at least 24 pixels of logical clearance. Relationship rendering SHALL preserve the existing physics-provided ports, lanes, bends, arrow direction, and endpoint clearance; DOM nodes SHALL remain the accessible and interactive source for node appearance, labels, selection, and drag input. The graph SHALL retain search, filter, zoom, pan, camera-only fit, drag, problem-count radius, focus, and the concise dashboard. Coordinates, soft anchors, motion, and interactions SHALL remain memory-only. If Web Worker support, graph physics resources, WebGL2, or renderer initialization is unavailable, the page SHALL show a readable graph error; a renderer startup failure after Worker creation SHALL terminate that Worker and release partial renderer resources. The page SHALL NOT run the synchronous solver or fall back to SVG.

#### Scenario: Read semantic spacing

- **WHEN** visible edges have different attraction
- **THEN** stronger relationships settle shorter than weaker relationships without allowing node circles to touch

#### Scenario: Lay out disconnected graph data

- **WHEN** the current graph contains several components and isolates
- **THEN** their deterministic seeds occupy separate readable regions before the unified field starts

#### Scenario: See a current graph state

- **WHEN** underlying knowledge-point state changes through a compatible explicit operation and the graph refreshes
- **THEN** live workspace data controls its visual presentation without exposing a manual state editor

#### Scenario: Read coverage and closeness

- **WHEN** nodes have different formal-problem counts and edges have different attraction
- **THEN** node radius expresses formal-problem count and stronger semantic edges retain shorter targets

#### Scenario: Navigate the graph directly

- **WHEN** the learner drags a node, pans, zooms, or fits the graph
- **THEN** the complete graph updates in memory and remains navigable

#### Scenario: Drag beyond the initial layout

- **WHEN** a learner drags a node beyond the initial graph region
- **THEN** its unbounded coordinate and a session-only soft anchor follow the pointer while edge proximity pans the camera

#### Scenario: Fit without rewriting layout

- **WHEN** the learner activates fit after freely placing nodes
- **THEN** only the camera changes and all node coordinates and soft anchors remain unchanged

#### Scenario: Focus without stealing the camera

- **WHEN** the learner selects a graph node
- **THEN** its one-hop and two-hop neighborhoods expand in place without automatic camera recentering

#### Scenario: Filter or resize the graph

- **WHEN** the learner searches, filters, or changes the available size
- **THEN** visible nodes receive deterministic seeds and the unified field reheats without persisting coordinates

#### Scenario: Filter the visible graph

- **WHEN** the learner searches or applies an available filter
- **THEN** visible nodes are reseeded and enter the unified field without persisting removed coordinates

#### Scenario: Inspect a focused node

- **WHEN** the learner focuses a node
- **THEN** the concise dashboard and neighborhood emphasis appear together

#### Scenario: Open the knowledge graph

- **WHEN** the learner activates the knowledge-graph navigation entry
- **THEN** the middle area displays the live complete chapter graph when graph execution and rendering are available, or a readable graph error when either is unavailable

#### Scenario: Graph artifact missing

- **WHEN** no rendered graph artifact exists on disk
- **THEN** the graph remains available from current workspace data

#### Scenario: Graph execution is unavailable

- **WHEN** the browser lacks Web Worker support or graph physics resources fail to load
- **THEN** the graph status explains that graph execution is unavailable, no synchronous solver is exposed or started, and authored and learning data remain unchanged

#### Scenario: Renderer startup fails

- **WHEN** the browser lacks WebGL2 support or graph renderer initialization fails after the Worker starts
- **THEN** the graph status shows a readable renderer error, the Worker terminates, pending solver and render frames stop, partial renderer resources are released, and authored and learning data remain unchanged

#### Scenario: Worker execution fails

- **WHEN** the Web Worker reports an execution error while the graph is settling
- **THEN** the Worker is terminated, the solver stops posting steps and scheduling solver frames, the graph status shows a readable error, and authored and learning data remain unchanged

#### Scenario: Preserve relationship geometry

- **WHEN** the relationship-structure view paints directed and parallel relations
- **THEN** their existing ports, lanes, bends, arrow direction, and endpoint clearance remain intact while graph nodes keep their labels, hit targets, selection, drag behavior, and accessibility

#### Scenario: Focus a selected neighborhood

- **WHEN** the learner selects a node
- **THEN** the node and one-hop neighbors remain fully emphasized, two-hop neighbors remain secondary, and farther topology fades

#### Scenario: Reset focus

- **WHEN** the learner selects the graph background
- **THEN** the complete graph returns to normal emphasis and ordinary semantic targets

#### Scenario: Reheat after interaction

- **WHEN** the learner filters, resizes, drags, focuses, or clears focus
- **THEN** the unified field reheats without persisting coordinates

#### Scenario: Prefer reduced motion

- **WHEN** the browser reports reduced motion
- **THEN** the graph settles and draws once without idle breathing
