## REMOVED Requirements

### Requirement: Living graph motion and readable labels

**Reason**: Its central clause — that canvas labels must always show the complete title,
wrapping instead of truncating — is reversed by this change at the owner's decision (D3).
The labels were long enough to cover neighbouring points and relationships, and their
width was also what forced the whole graph to stay large and the view zoomed out. A
requirement whose main assertion is being reversed cannot be expressed as a modification
that keeps its scenarios, so it is removed and replaced by `Living graph motion and quiet
labels`, which keeps the motion clauses and states the new label rules.

### Requirement: Adjustable graph compactness

**Reason**: It specifies the 0–100 control as a centre-gravity control with a maximum
coefficient of about 0.00351. Measurement showed that control had no effect worth having:
across its full travel the settled graph changed size by 3.5% and mean relationship length
by 1.6%, because the mechanism actually deciding the layout was not the one the control
moved. The owner's decision (D4) is to rebind it to repulsion, which is a different
control with a different meaning, so it is removed and replaced by `Node spacing control`.

## ADDED Requirements

### Requirement: Frame motion is continuous

Per-frame motion SHALL be limited by velocity damping rather than by a fixed speed
ceiling, so that the fastest points are not pinned at a cutoff. No point position SHALL
be written outside the integration step by anything other than the forces named in
`Free force field layout`.

#### Scenario: No speed ceiling

- **WHEN** a point accumulates velocity from a large force
- **THEN** its step is scaled by the damping, not clamped to a fixed constant

#### Scenario: Settling decelerates

- **WHEN** the solve runs to rest
- **THEN** per-frame displacement decreases monotonically and the direction of motion rarely reverses

### Requirement: Repulsion is foldable

Repulsion SHALL be computed by folding distant groups of points into a single point
charge rather than by visiting every pair. The folding threshold and near-field floor
SHALL be the reference's measured values. Point ordering and layout meaning SHALL NOT
change.

#### Scenario: Distant groups fold

- **WHEN** a group of points is far enough away relative to its own extent
- **THEN** its members act as one point charge at their centroid

#### Scenario: Coincident points do not hang the solve

- **WHEN** two points occupy the same position
- **THEN** they share a leaf and the fold does not recurse forever

### Requirement: Free force field layout

The structure projection SHALL let the force field alone decide where points settle. No
mechanism other than the four forces (spring, charge, collision, centring) and the
integrator SHALL write a point's position, and no mechanism SHALL impose a stage boundary,
a row band, or a guaranteed minimum separation on settled points.

The starting arrangement SHALL be derived from the graph's own connectivity rather than
from a page-layout grid, so that linked points begin near each other and the first
simulated frame is not a jump.

#### Scenario: A wider force setting produces a wider graph

- **WHEN** the learner raises the repulsion
- **THEN** the settled graph is measurably larger, and no other mechanism holds the points in place instead

#### Scenario: The graph finds its own extent

- **WHEN** the settled graph is wider than the stage rectangle
- **THEN** the points stay where the forces put them and the view fits them, rather than being clamped back inside

#### Scenario: The first frame is not a jump

- **WHEN** the graph is built from a course with relationships
- **THEN** no point moves further on the first simulated frame than it does on an average frame by an order of magnitude

#### Scenario: An unlinked point stays in the picture

- **WHEN** a knowledge point has no relationships at all
- **THEN** it settles within the extent of the linked points rather than outside it, and it carries no marking that would imply it has relationships

#### Scenario: The shape reflects the data

- **WHEN** the same course is laid out
- **THEN** the graph's aspect ratio is not driven by the shape of the stage or of any guide grid

### Requirement: Living graph motion and quiet labels

The graph SHALL remain fully static after the force simulation settles. It SHALL reheat
only after a learner interaction or viewport/model change such as dragging, filtering,
focusing, resizing, or changing the spacing control. It SHALL NOT apply a continuous idle
breathing offset.

On the canvas a knowledge point SHALL be labelled with a short name derived from its
title, and the complete title SHALL remain reachable by hover and in the detail panel. The
short name SHALL be the title up to its first punctuation other than a comma. Where two
points would otherwise share a short name, those points SHALL be extended to their next
punctuation so that no two points on the canvas carry the same label. Label extent SHALL
participate in the spacing the layout targets, so a label does not cover a neighbouring
point or relationship.

Because the layout is free, that spacing SHALL be understood as a target rather than a
guarantee: the collision force approaches it and does not impose it, and a settled layout
MAY therefore contain a small number of pairs closer together than their target. The graph
SHALL NOT advertise a guarantee it does not enforce.

The projection pipeline (how artifacts are derived from source material at ingest) SHALL
NOT change; only the runtime presentation layout is affected.

#### Scenario: Settled graph is quiet

- **WHEN** the graph simulation reaches its stable threshold and the learner does nothing
- **THEN** node and label positions remain unchanged and no recurring animation loop is scheduled

#### Scenario: Pause a hidden graph

- **WHEN** the document becomes hidden
- **THEN** any active settling frames stop until a later interaction or visibility change resumes the simulation

#### Scenario: See a quiet living graph

- **WHEN** an ordinary-motion graph finishes active settling and remains visible
- **THEN** its nodes remain still without random or periodic displacement

#### Scenario: Read graph labels

- **WHEN** the learner changes zoom, search, hover, or focus
- **THEN** labels follow the existing readable visibility and emphasis rules

#### Scenario: Read progressively disclosed labels

- **WHEN** the learner changes zoom, search, hover, or focus
- **THEN** the corresponding ranked or explicitly relevant labels remain readable under the defined thresholds

#### Scenario: Read a short name

- **WHEN** a knowledge point's title continues past its opening phrase with punctuation
- **THEN** the canvas shows only the opening phrase, and the complete title appears on hover and in the detail panel

#### Scenario: Two points never share a canvas label

- **WHEN** shortening two or more titles would produce the same label
- **THEN** each of those points is labelled with enough of its title to tell them apart

#### Scenario: The spacing target is met, not guaranteed

- **WHEN** the simulation settles
- **THEN** the great majority of point pairs are at or above their target spacing, and any that are not are a documented consequence of the free layout rather than a hidden failure

### Requirement: Node spacing control

The existing 0–100 in-memory control SHALL control how closely points settle, by scaling
the repulsive force. It SHALL NOT be a centre-gravity control. Its default SHALL be 30.
Raising it SHALL settle the graph tighter and lowering it SHALL let the graph spread, by a
margin visible across the control's full travel. The value SHALL NOT be persisted or
written to learning records.

#### Scenario: Tighten the graph

- **WHEN** the learner raises the control
- **THEN** the simulation reheats with stronger repulsion and the settled graph is visibly tighter

#### Scenario: Loosen the graph

- **WHEN** the learner lowers the control
- **THEN** the simulation reheats with weaker repulsion and the settled graph is visibly larger

#### Scenario: The control is not decorative

- **WHEN** the settled graph is measured at the lowest and the highest setting
- **THEN** its size differs by a margin large enough to see on screen, not by a few percent

## MODIFIED Requirements

### Requirement: Complete primary learning text

The workbench SHALL display user-authored knowledge titles, questions, notes, goal titles,
and practice-scope titles in full wherever that text is the primary content of a panel,
list, or detail view. Those labels SHALL wrap within their available column and SHALL NOT
use ellipsis. Flex and grid containers around them SHALL allow content children to shrink
without widening the three-column shell.

The knowledge-graph canvas is not such a place: it is a map rather than a reading surface.
It shows the short name described in `Living graph motion and quiet labels` and keeps the
complete title one hover away, and shortening it there SHALL NOT be read as truncating the
learner's text.

#### Scenario: Long unbroken title

- **WHEN** a primary title contains a string wider than its column
- **THEN** it wraps inside the column without clipping or widening the page

#### Scenario: Practice scope title

- **WHEN** a practice-scope title is longer than its column
- **THEN** it wraps in full without ellipsis and without widening the shell

#### Scenario: The canvas is a map, not a reading surface

- **WHEN** a knowledge point with a long title appears on the graph canvas
- **THEN** the canvas shows its short name while the complete title is unchanged in the data and visible on hover and in the detail panel
