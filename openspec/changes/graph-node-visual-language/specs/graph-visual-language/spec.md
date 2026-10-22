## Purpose

The graph visual language defines how a knowledge-graph node looks and how a
learner reads a dense chapter at a glance: the single solid-circle node form,
the screen-space sizing that keeps a fitted graph legible, the colour key each
projection carries, the legend that follows the projection, the label rules,
the relationship-line rules, the night-paper adaptation, the selection
emphasis — and the boundary that keeps the graph's layout algorithm untouched.
It fixes what a node may show, what it must never show, which words are not
allowed on the node, and which parts of the graph must not move.

## ADDED Requirements

### Requirement: Node appearance language

Every graph node SHALL be drawn as a single solid circle filled with one flat
colour. The node SHALL carry no visible outline, no drop shadow, no glow, no
gradient, no inner highlight and no visible halo. The node centre SHALL carry
a number only under the formal-problem-count and importance projections, where
that number SHALL be the value of the active projection — the count of formal
problems for the formal-problem-count projection, and the rounded importance
percentage for the importance projection. Under the relationship-structure and
learning-state projections the node centre SHALL carry no number at all, and
no projection SHALL place any state word, progress arc, gauge, badge or
satellite marker on a node. The node's learning state SHALL be expressed by its
colour together with the geometry of its radius and its radial position under
the active projection, and the node's accessible name SHALL continue to expose
that state to assistive technology. Node appearance SHALL be derived only from
the node's own learning state, formal-problem count, importance and
relationship degree under the active projection; the graph SHALL NOT introduce
any additional state source, state editor or per-node state control.

#### Scenario: Read a node as one solid circle

- **WHEN** the graph draws a node
- **THEN** it is drawn as one flat filled circle with no outline, drop shadow, glow, gradient, inner highlight or visible halo

#### Scenario: Read the number at the node centre

- **WHEN** the graph draws a node under the formal-problem-count or importance projection
- **THEN** its centre shows only the active projection's value — the count of formal problems, or the rounded importance percentage — and the two projections never show the same value for the same node

#### Scenario: Read a structure or state node without a number

- **WHEN** the graph draws a node under the relationship-structure or learning-state projection
- **THEN** no number is drawn at its centre, because the structure is carried by the relationship lines and the learning state is carried by colour

#### Scenario: Read a state without words on the node

- **WHEN** a node has a formal learning state
- **THEN** no state word is drawn on the node, the state is expressed by its colour together with its radius and radial position, and the node's accessible name still names the state

#### Scenario: Nodes add no new state source

- **WHEN** the graph renders
- **THEN** every node's appearance is derived from its own learning state, formal-problem count, importance and relationship degree under the active projection, and no additional state source, state editor or per-node state control is introduced

### Requirement: Screen-space sizing

Node radius, node label text size, the gap between a node and its label, and
relationship-line width SHALL be specified in screen pixels so that the stage's
zoom transform does not shrink them; zooming the graph SHALL change only the
spacing between nodes and not the size of anything drawn. The drawn node
radius SHALL lie between 5 and 13 screen pixels. Under the relationship-structure
projection the radius SHALL follow the node's relationship degree
monotonically, and under the learning-state projection it SHALL follow the
active projection's metric monotonically, so that equal metric values receive
equal radii. Under the formal-problem-count and importance projections the
radius SHALL likewise follow the active projection's metric monotonically, so
that a higher metric value still takes a larger node, and SHALL NOT be smaller
than 6.5 screen pixels — a diameter of 13 screen pixels — so that the centre
number fits inside the circle without the radius being held at a constant
size. Node label text SHALL be rendered at 12 screen pixels. The drawn
radius SHALL be derived from the node's metric in the same order as the
physical radius used by the layout, and the physical radius SHALL NOT be
changed by this language.

#### Scenario: A fitted graph stays legible

- **WHEN** a chapter graph is fitted to the viewport
- **THEN** every drawn node radius stays between 5 and 13 screen pixels — and under the formal-problem-count and importance projections never below 6.5 screen pixels — and each node's centre number and label stay readable without zooming in

#### Scenario: Labels use the pinned screen-space size

- **WHEN** a node label is drawn
- **THEN** its text size is 12 screen pixels, unaffected by the stage's zoom transform

#### Scenario: Zooming changes spacing, not size

- **WHEN** the learner zooms the graph in or out
- **THEN** node radii, label text sizes, node-to-label gaps and relationship-line widths keep their screen-pixel values, and only the spacing between nodes changes

#### Scenario: Equal values get equal sizes

- **WHEN** two nodes have the same value in the active projection
- **THEN** they are drawn with the same radius, in every projection including the formal-problem-count and importance projections

#### Scenario: The layout radius is not changed by the drawing

- **WHEN** the graph draws a node
- **THEN** the drawn radius follows the node's metric in the same order as the physical radius the layout uses, and the physical radius itself is unchanged

### Requirement: Projection colour keys

Each graph projection SHALL carry its own colour key. The relationship-structure
projection SHALL use a three-step ink scale and SHALL NOT encode relationship
meaning in node colour. The formal-problem-count and importance projections
SHALL use one hue in graded steps, with a higher metric value taking a stronger
step. The learning-state projection SHALL use four categorical colours: a
neutral grey for an unmarked state, amber for review, orange for mastered, and
a brick red for a state that needs work. These colour keys belong to the graph and
SHALL NOT be limited by the workbench's site-wide accent-role quota. Every node
fill colour SHALL reach a contrast of at least 3 to 1 against the paper it is
drawn on, and a centre number SHALL reach a contrast of at least 4.5 to 1
against the fill it sits on. Changing the active projection SHALL change colours
only, and SHALL NOT change or write any learning record, learning state, schedule
or graph membership.

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

#### Scenario: Every node fill is visible on the paper

- **WHEN** a node is drawn on either paper theme
- **THEN** its fill colour reaches a contrast of at least 3 to 1 against that paper, and any centre number reaches at least 4.5 to 1 against its own fill

#### Scenario: Colour changes no learning data

- **WHEN** the learner changes the active projection
- **THEN** only the graph's colours change, and no learning record, learning state, schedule or graph membership is changed or written

### Requirement: Label legibility and decluttering

Node labels SHALL be drawn below the node, with the gap from the node's lower
edge to the top of the label text at 5 screen pixels, so that a label never
overlaps its own node. Node labels SHALL be visible by default and SHALL be
drawn at a contrast lower than the node's own fill, so that they do not compete
with the node. As the graph is zoomed out below a scale of 0.5, node labels
SHALL fade out logarithmically rather than shrinking further, and a label that
is hidden by overlap SHALL become readable again when the learner hovers or
selects its node. A node label SHALL be hidden automatically when it overlaps a
label of higher priority, where priority is decided by node size and then by
importance, and the graph SHALL keep a bounded budget of simultaneously drawn
labels, applying the same ranking when that budget is exceeded. Hiding labels
SHALL NOT change graph membership, node positions, or any learning data.

#### Scenario: Labels sit below their node

- **WHEN** a node and its label are drawn
- **THEN** the label is drawn below the node with 5 screen pixels between the node's lower edge and the top of the label text, and they do not overlap

#### Scenario: Labels are visible by default

- **WHEN** the graph settles
- **THEN** node labels are drawn at a contrast lower than the node fill, within the graph's visible-label budget

#### Scenario: Labels fade out when zoomed far out

- **WHEN** the learner zooms the graph below a scale of 0.5
- **THEN** node labels fade out logarithmically as the scale decreases instead of shrinking further, and at the default fitted scale the labels are fully visible

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
relationship line styles, including which of them are drawn with a direction
arrow, and a lower part showing the node colours of the active projection. The
node-colour part SHALL switch with the active projection and SHALL name the
colour meaning it shows. The legend SHALL NOT introduce a learning state,
metric or filter control.

#### Scenario: Read the relationship key

- **WHEN** the learner looks at the graph legend
- **THEN** its upper part lists the relationship line styles and marks which of them carry a direction arrow

#### Scenario: Read the node colour key

- **WHEN** the learner switches to the learning-state projection
- **THEN** the legend's lower part shows the four learning-state colours with their names

#### Scenario: The node key follows the projection

- **WHEN** the learner changes the active projection
- **THEN** the legend's lower part changes to that projection's colour key

### Requirement: Night paper graph adaptation

On the night paper theme the graph SHALL keep the same hue families as the light
theme, rendered lighter and less saturated, and its node fills, centre numbers,
relationship lines and labels SHALL stay legible against the dark surface. On
the light theme the graph SHALL remain at least as legible as before this change:
after the graph is fitted, every node's fill, centre number and label SHALL be
readable without zooming in, and a node SHALL be visibly filled rather than
empty paper. Theme adaptation SHALL change colours only, and SHALL NOT change
graph membership, layout, learning data or any projection behaviour.

#### Scenario: Night paper keeps the hue

- **WHEN** the workbench uses the night paper theme
- **THEN** the graph's node colours keep the same hue families as on the light theme, rendered lighter and less saturated

#### Scenario: Night paper stays readable

- **WHEN** the graph is shown on the night paper theme
- **THEN** node fills, centre numbers, relationship lines and labels remain legible against the dark surface

#### Scenario: The light theme does not regress

- **WHEN** the learner fits a chapter graph on the light theme after this change
- **THEN** every node's fill, centre number and label are readable without zooming in, and each node is visibly filled rather than empty paper

### Requirement: Selection and focus

A selected or hovered node SHALL be marked by a change of fill colour, a thin
one-pixel outline ring drawn just outside the node, a slightly larger size, and
a brighter label. The outline ring SHALL be one screen pixel wide at every zoom
level. The ordinary, unselected node SHALL carry no outline ring at all. Node
emphasis SHALL NOT use a drop shadow, a glow halo, or a satellite point.
Selecting, hovering or focusing a node SHALL NOT change graph membership,
layout, or any learning data, and SHALL NOT change the node's physical radius.

#### Scenario: Selected node

- **WHEN** the learner selects a node
- **THEN** its fill changes to the most solid step, a one-pixel ring is drawn just outside it, it grows slightly and its label becomes brighter

#### Scenario: Hover does not select

- **WHEN** the learner hovers a node that is not selected
- **THEN** the same emphasis appears and the selection is unchanged

#### Scenario: Emphasis is not a shadow

- **WHEN** a node is selected, hovered or focused
- **THEN** it is marked by its colour, its thin ring, its size and its label alone, with no drop shadow, glow halo or satellite point

#### Scenario: Emphasis does not move the graph

- **WHEN** a node is selected, hovered or focused
- **THEN** the node's physical radius and the graph's layout are unchanged

### Requirement: Relationship lines meet the node dot

Relationship lines SHALL be drawn as straight lines whose width stays constant
in screen pixels and whose base opacity is 0.3. Their endpoints SHALL terminate
at the outer edge of the node's drawn circle, so that a line meets the node
instead of running into its centre. A relationship type that carries direction
SHALL be drawn with a direction arrow at the target end, and a relationship
type that carries no direction SHALL be drawn without an arrow: the
prerequisite and application types are directed, while the contrast, related
and implied types are symmetric or undirected and carry no arrow. When a node
is selected, the lines connected to it SHALL stay fully visible, lines to
second-order neighbours SHALL remain secondary, and lines to the rest of the
graph SHALL fade to an opacity of 0.2 rather than disappearing. Relationship
lines SHALL NOT introduce, remove, retype or reverse any relationship.

#### Scenario: A line meets the node dot

- **WHEN** a relationship is drawn between two nodes
- **THEN** it ends at the outer edge of each node's drawn circle, and its width stays constant in screen pixels

#### Scenario: Read a directed relationship

- **WHEN** a prerequisite or application relationship is drawn
- **THEN** it carries a direction arrow at the target end, pointing from the source to the target

#### Scenario: Read an undirected relationship

- **WHEN** a contrast, related or implied relationship is drawn
- **THEN** it carries no direction arrow

#### Scenario: Focus fades the far lines without hiding them

- **WHEN** a node is selected
- **THEN** the lines connected to it stay fully visible, second-order lines stay secondary, and the remaining lines fade to an opacity of 0.2 rather than disappearing

#### Scenario: Relationship lines change no relationship

- **WHEN** the graph draws its relationship lines
- **THEN** no relationship is added, removed, retyped or reversed, and the relationships' weights are unchanged

### Requirement: Graph layout algorithm is frozen

The graph's layout algorithm SHALL NOT be changed by the node visual language.
The force model, the iteration count, the convergence criterion, the damping,
the attraction and repulsion parameters, the collision and separation of nodes,
the layout seed, the adjacency and edge set, the relationship types and their
weights, the filtering semantics, the projection semantics and their banding,
the metric computation, the identity and order of the DOM nodes, and the
behaviour semantics of dragging and focusing SHALL all stay exactly as they
were. The same input SHALL converge to the same node coordinates before and
after the change: running the force layout on the same chapter, from the same
initial condition and with the same iteration budget, SHALL produce a
converged node coordinate set that matches item by item.

#### Scenario: The layout converges to the same coordinates

- **WHEN** the force layout is run on the same chapter before and after the change, from the same initial condition and with the same iteration budget
- **THEN** the converged coordinate of every node is identical in both runs, with no differing node

#### Scenario: The layout parameters are unchanged

- **WHEN** the change is inspected
- **THEN** the force model, iteration count, convergence criterion, damping, attraction and repulsion parameters, collision and separation logic, layout seed, edge set and weights, filtering semantics, projection semantics, metric computation, DOM node identity and order, and drag and focus behaviour are unchanged
