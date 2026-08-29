## MODIFIED Requirements

### Requirement: Living graph motion and readable labels

The graph SHALL remain fully static after the force simulation settles. It
SHALL reheat only after a learner interaction or viewport/model change such
as dragging, filtering, focusing, resizing, or changing global gravity. It
SHALL NOT apply a continuous idle breathing offset. Labels SHALL remain
readable under the existing focus and zoom rules, and raw identifiers SHALL
NOT be primary canvas text. Node labels SHALL always display their complete
text — wrapping to multiple lines instead of truncating — and label extent
SHALL participate in collision spacing so wrapped labels do not overlap
each other or nearby nodes. The projection pipeline (how artifacts are
derived from source material at ingest) SHALL NOT change; only the runtime
presentation layout is affected.

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

#### Scenario: A long node label stays complete

- **WHEN** a knowledge-point title is longer than one label line
- **THEN** the label wraps to further lines and shows its full text without
  truncation or ellipsis, and collision spacing accounts for the wrapped
  extent

## ADDED Requirements

### Requirement: Complete text display across surfaces

Item labels and chips across the workbench SHALL display their complete text:
due-item labels and calendar goal chips SHALL wrap to additional
lines instead of being truncated, clipped, or ellipsized. Calendar cells
SHALL grow in height to fit fully displayed goal chips. An overlong name is
a content-naming matter — the UI SHALL NOT mitigate it by hiding text.

#### Scenario: Long due-item label

- **WHEN** a due item's label text exceeds one line
- **THEN** the row wraps and shows the full text with no character cap

#### Scenario: Calendar chip with a long goal title

- **WHEN** a day cell holds a goal whose title is longer than the cell width
- **THEN** the goal chip wraps inside the cell and the cell grows to show
  the full title
