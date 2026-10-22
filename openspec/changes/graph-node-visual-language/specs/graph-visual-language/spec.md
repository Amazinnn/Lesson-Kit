## Purpose

The graph visual language defines how a knowledge-graph node looks and how a
learner reads a dense chapter at a glance: the concentric two-circle node form,
the screen-space sizing that keeps a fitted graph legible, the colour key each
projection carries, the legend that follows the projection, the label rules, the
night-paper adaptation and the selection emphasis. It fixes what a node may
show, what it must never show, and which words are not allowed on the node.

## ADDED Requirements

### Requirement: Node appearance language

Every graph node SHALL be drawn as two concentric circles in one hue: a light
inner core inside a solid outer ring. The node centre SHALL carry exactly one
number, the count of formal problems linked to that node, and the same count
SHALL be shown in every projection. A node SHALL NOT carry a visible state word,
a progress arc, a gauge, a satellite marker, a drop shadow or a glow. A node's
learning state SHALL be expressed by its colours together with the geometry of
its concentric rings, and the node's accessible name SHALL continue to expose
that state to assistive technology. Node appearance SHALL be derived only from
the node's own learning state, formal-problem count, importance and relationship
degree under the active projection; the graph SHALL NOT introduce any additional
state source, state editor or per-node state control.

#### Scenario: Read a node as two concentric circles

- **WHEN** the graph draws a node
- **THEN** it is drawn as a light inner core inside a solid outer ring of the same hue, with no progress arc, gauge, satellite marker, drop shadow or glow on it

#### Scenario: Read the number at the node centre

- **WHEN** the graph draws a node in any projection
- **THEN** its centre shows only the count of formal problems linked to that node, and the same count is shown in every projection

#### Scenario: Read a state without words on the node

- **WHEN** a node has a formal learning state
- **THEN** no state word is drawn on the node, the state is expressed by its colours and the geometry of its concentric rings, and the node's accessible name still names the state

#### Scenario: Nodes add no new state source

- **WHEN** the graph renders
- **THEN** every node's appearance is derived from its own learning state, formal-problem count, importance and relationship degree under the active projection, and no additional state source, state editor or per-node state control is introduced

### Requirement: Projection colour keys

Each graph projection SHALL carry its own colour key. The relationship-structure
projection SHALL use a three-step ink scale and SHALL NOT encode relationship
meaning in node colour. The formal-problem-count and importance projections
SHALL use one hue in graded steps, with a higher metric value taking a stronger
step. The learning-state projection SHALL use four categorical colours: a
neutral grey for an unmarked state, amber for review, orange for mastered, and a
brick red for a state that needs work. These colour keys belong to the graph and
SHALL NOT be limited by the workbench's site-wide accent-role quota. Changing
the active projection SHALL change colours only, and SHALL NOT change or write
any learning record, learning state, schedule or graph membership.

#### Scenario: Read a magnitude projection

- **WHEN** the learner selects the formal-problem-count or importance projection
- **THEN** node colour is one hue in graded steps, and a higher metric value takes a stronger step

#### Scenario: Read the state key

- **WHEN** the learner selects the learning-state projection
- **THEN** each node takes its learning state's colour — neutral grey for unmarked, amber for review, orange for mastered, and brick red for a state that needs work

#### Scenario: Read the structure key

- **WHEN** the learner selects the relationship-structure projection
- **THEN** each node takes one of three ink steps, and node colour carries no relationship meaning because relationship types are shown by the edge line styles

#### Scenario: The graph keeps its own palette

- **WHEN** graph colours are shown
- **THEN** the graph's colour keys are not limited by the workbench's site-wide accent-role quota

#### Scenario: Colour changes no learning data

- **WHEN** the learner changes the active projection
- **THEN** only the graph's colours change, and no learning record, learning state, schedule or graph membership is changed or written

### Requirement: Screen-space sizing

Node diameter, node label text size and small-dot diameter SHALL be specified in
screen pixels so that the stage's zoom transform does not shrink them. Node
radius SHALL map continuously from 14 to 30 screen pixels across the active
projection's metric range, and equal metric values SHALL receive equal radii.
Zooming the graph out SHALL NOT shrink a node below its screen-space size, and a
graph fitted to the viewport SHALL keep every node's centre number and label
readable without zooming in.

#### Scenario: A fitted graph stays legible

- **WHEN** a chapter graph is fitted to the viewport
- **THEN** node radii stay between 14 and 30 screen pixels, and each node's centre number and label stay readable without zooming in

#### Scenario: Zooming out does not shrink a node

- **WHEN** the learner zooms the graph out
- **THEN** node diameters, label text sizes and small-dot diameters do not shrink below their screen-space values

#### Scenario: Equal values get equal sizes

- **WHEN** two nodes have the same value in the active projection
- **THEN** they are drawn with the same radius

### Requirement: Label legibility and decluttering

Node labels SHALL be visible by default and SHALL be drawn at a contrast lower
than the node's own fill, so that they do not compete with the node. A node
label SHALL be hidden automatically when it overlaps a label of higher priority,
where priority is decided by node size and then by importance, and the graph
SHALL keep a bounded budget of simultaneously drawn labels, applying the same
ranking when that budget is exceeded. A label that has been hidden SHALL become
readable again when the learner hovers or selects its node. Hiding labels SHALL
NOT change graph membership, node positions, or any learning data.

#### Scenario: Labels are visible by default

- **WHEN** the graph settles
- **THEN** node labels are drawn at a contrast lower than the node fill, within the graph's visible-label budget

#### Scenario: Overlapping labels yield

- **WHEN** two node labels would overlap
- **THEN** the label of the smaller or less important node is hidden and the other stays readable

#### Scenario: A hidden label returns

- **WHEN** a label has been hidden by overlap or by the visible-label budget
- **THEN** hovering or selecting that node shows its label again

#### Scenario: Decluttering changes nothing else

- **WHEN** labels are hidden
- **THEN** graph membership, node positions and learning data are unchanged

### Requirement: Graph colour legend follows the projection

The graph's legend SHALL be split into two parts: an upper part listing the
relationship line styles, and a lower part showing the node colours of the
active projection. The node-colour part SHALL switch with the active projection
and SHALL name the colour meaning it shows. The legend SHALL explain colours
only, and SHALL NOT introduce a learning state, metric or filter control.

#### Scenario: Read the relationship key

- **WHEN** the learner looks at the graph legend
- **THEN** its upper part lists the relationship line styles

#### Scenario: Read the node colour key

- **WHEN** the learner switches to the learning-state projection
- **THEN** the legend's lower part shows the four learning-state colours with their names

#### Scenario: The node key follows the projection

- **WHEN** the learner changes the active projection
- **THEN** the legend's lower part changes to that projection's colour key

### Requirement: Night paper graph adaptation

On the night paper theme the graph SHALL keep the same hue families as the light
theme, rendered lighter and less saturated, and its node fills, outer rings,
relationship lines and labels SHALL stay legible against the dark surface. On the
light theme the graph SHALL remain at least as legible as before this change:
after the graph is fitted, every node's outer ring, centre number and label
SHALL be readable without zooming in, and a node's inner area SHALL be visibly
filled rather than empty paper. Theme adaptation SHALL change colours only, and
SHALL NOT change graph membership, layout, learning data or any projection
behaviour.

#### Scenario: Night paper keeps the hue

- **WHEN** the workbench uses the night paper theme
- **THEN** the graph's node colours keep the same hue families as on the light theme, rendered lighter and less saturated

#### Scenario: Night paper stays readable

- **WHEN** the graph is shown on the night paper theme
- **THEN** node fills, outer rings, relationship lines and labels remain legible against the dark surface

#### Scenario: The light theme does not regress

- **WHEN** the learner fits a chapter graph on the light theme after this change
- **THEN** every node's outer ring, centre number and label are readable without zooming in, and each node's inner area is visibly filled rather than empty paper

### Requirement: Selection and focus

A selected node SHALL be marked by a thicker, solid outer ring and a slightly
larger size. Hovering or focusing a node SHALL apply the same ring emphasis
without changing the selection. Node emphasis SHALL NOT use a drop shadow, a
glow halo, or a satellite point. Selecting, hovering or focusing a node SHALL
NOT change graph membership, layout, or any learning data.

#### Scenario: Selected node

- **WHEN** the learner selects a node
- **THEN** its outer ring becomes thicker and solid and the node grows slightly

#### Scenario: Hover does not select

- **WHEN** the learner hovers a node that is not selected
- **THEN** the same ring emphasis appears and the selection is unchanged

#### Scenario: Emphasis is not a shadow

- **WHEN** a node is selected, hovered or focused
- **THEN** it is marked by its outer ring and its size alone, with no drop shadow, glow halo or satellite point

### Requirement: Relationship lines meet the node ring

Relationship lines SHALL keep their existing line styles, widths, colours and
layered pipe construction. Their endpoints SHALL terminate at the outer edge of
the node's outer ring, so that a line meets the ring instead of running into
the node's centre.

#### Scenario: A line meets the ring

- **WHEN** a relationship is drawn between two nodes
- **THEN** it ends at the outer edge of each node's outer ring, and its line style, width and colour are unchanged
