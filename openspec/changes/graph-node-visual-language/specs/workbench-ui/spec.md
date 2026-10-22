> **⚠️ 归档顺序（A-10.2，硬性、不可颠倒）**
>
> 本 delta 中的 `Redundant state cues` 与 `Soft Mondrian visual foundation`
> 两个 MODIFIED 块**必须先合入 `workbench-visual-language-v2`，
> 再 re-base 到 v2 的版本上** —— v2 的 pending delta **已经** MODIFIED 了这两条；
> 本变更若先落地，会**覆盖 v2 已写的扩展内容**。
>
> ⇒ **这两块当前的正文是「v2 之前的基线文本」，属占位文本，不是最终文本**
> （v2 尚未归档，现在无法 re-base）。
> ⇒ 归档动作（两件，缺一不可）：① **先归档 `workbench-visual-language-v2`**，
> 再归档本变更；② 归档本变更前**逐字复核**这两条需求的最终文本，
> 确认它是「**v2 的版本 + 本变更的图谱例外段落**」的合流结果，
> 而不是本变更的旧基线文本；re-base 时**一并删掉下面两处块内标注**。
>
> 另：**A-10.3 标签不截断** —— 下面 `Living graph motion and readable labels` 取
> 「**不截断**」的一支（换行显示全文，完整标题由悬浮 / 键盘聚焦承载），
> 与 G-23（重叠时**隐藏**次要标签）是**两个不同机制**，互不冲突。
> 又：节点半径区间以新能力 `graph-visual-language` 的 `Screen-space sizing` 为准
> （**14–30 屏幕像素**，A-10.1 收窄后）；本 delta 不另写半径数值。

## MODIFIED Requirements

### Requirement: Knowledge graph page

When browser Web Worker support, graph physics resources, and WebGL2 support are available, the knowledge graph page SHALL render the live complete chapter graph in a middle-column canvas that fills the viewport below its compact page tools. Six deterministic component layouts SHALL supply seed positions before every visible node enters one unbounded unified elastic field. Existing edge attraction SHALL determine variable semantic gaps from 72 to 144 pixels in addition to endpoint radii, and every pair of node circles SHALL retain at least 24 pixels of logical clearance. Relationship rendering SHALL preserve the existing physics-provided ports, lanes, bends, arrow direction, and endpoint clearance; DOM nodes SHALL remain the accessible and interactive source for node appearance, labels, selection, and drag input. The graph SHALL retain search, filter, zoom, pan, camera-only fit, drag, projection-driven node radius sized in screen pixels, focus, and the concise dashboard. Every node SHALL be drawn in the graph's node appearance language — two concentric circles in one hue, one formal-problem count at the centre, and no state word, progress arc, satellite marker, drop shadow or glow on the node — and node labels SHALL be visible by default at a contrast below the node's own fill. The graph's colour legend SHALL switch its node-colour key with the active projection. Viewport culling and label/meta LOD SHALL affect paint only; a node label SHALL be hidden only where it overlaps a label of higher priority or exceeds the graph's visible-label budget; for on-screen nodes, selected, hovered, and high-focus labels SHALL remain visible at reduced zoom, and graph membership and selection SHALL remain available. When browser `localStorage` is available, the graph runtime SHALL keep at most one optional settled local layout seed per workspace. Its readable identity SHALL contain the sorted node IDs and sorted relationship tuples of source, target, type, and direction. The graph SHALL read a seed only when its identity exactly matches the current graph, restore its coordinates as temporary anchors through the existing Worker, then release those anchors and reheat that same Worker. Filters, selection, motion, active anchors, authored content, and learning state SHALL NOT be restored from the seed. Missing, stale, corrupt, or unavailable storage SHALL leave the deterministic Worker startup unchanged. If Web Worker support, graph physics resources, WebGL2, or renderer initialization is unavailable, the page SHALL show a readable graph error; a renderer startup failure after Worker creation SHALL terminate that Worker and release partial renderer resources. The page SHALL NOT run the synchronous solver or fall back to SVG.

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
- **THEN** node radius expresses the formal-problem count in the projection that measures formal problems, and stronger semantic edges retain shorter targets

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
- **THEN** visible nodes receive deterministic seeds and the unified field reheats without restoring filters or selection from a local layout seed

#### Scenario: Filter the visible graph

- **WHEN** the learner searches or applies an available filter
- **THEN** visible nodes are reseeded and enter the unified field while filter state remains page-only and stale topology seeds are not reused

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
- **THEN** the unified field reheats from current in-memory positions and any later settled seed remains limited to the current graph identity

#### Scenario: Prefer reduced motion

- **WHEN** the browser reports reduced motion
- **THEN** the graph settles and draws once without idle breathing

#### Scenario: Restore a matching local layout seed

- **WHEN** a settled seed exists for the current workspace and its readable graph identity exactly matches the current nodes and relationships
- **THEN** its coordinates become temporary Worker anchors, are released, and the same deterministic Worker reheats and settles the graph

#### Scenario: Ignore an unusable local layout seed

- **WHEN** the stored seed is stale, corrupt, has an unsupported version, or browser storage is blocked or unavailable
- **THEN** the graph starts with the normal deterministic Worker layout without a graph error or a fallback solver

#### Scenario: Keep the layout seed outside authored and learning data

- **WHEN** the graph reads, writes, or loses its optional local layout seed
- **THEN** authored relations, content, filters, selection, learner state, signals, and schedules remain unchanged, and clearing the browser cache loses only the layout starting point

#### Scenario: Keep viewport LOD paint-only

- **WHEN** the learner changes zoom or viewport or the renderer repaints
- **THEN** off-screen node wrappers may be hidden and label/meta detail may be reduced, while graph membership and selection remain available and on-screen selected, hovered, and high-focus labels remain visible at reduced zoom

#### Scenario: Read the graph's node visual language

- **WHEN** the learner opens the knowledge graph page
- **THEN** each node is drawn as a light inner core inside a solid outer ring of the same hue with one formal-problem count at its centre, its label is drawn at a contrast below the node fill, and the legend's node-colour key matches the active projection

### Requirement: Living graph motion and readable labels

The graph SHALL remain fully static after the force simulation settles. It
SHALL reheat only after a learner interaction or viewport/model change such
as dragging, filtering, focusing, resizing, or changing global gravity. It
SHALL NOT apply a continuous idle breathing offset. Labels SHALL remain
readable under the graph's label legibility and decluttering rules, and raw
identifiers SHALL NOT be primary canvas text. Node labels SHALL display their
complete text without ellipsis or a character cap whenever they are shown —
wrapping to further lines instead of truncating — and label extent SHALL
participate in collision spacing so wrapped labels do not overlap each other
or nearby nodes. Labels SHALL be hidden only by the graph's label decluttering
rules, and a node's complete title SHALL remain available to the learner on
hover and keyboard focus. The projection pipeline (how artifacts are derived
from source material at ingest) SHALL NOT change; only the runtime presentation
layout is affected.

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
- **THEN** labels follow the graph's label legibility, decluttering and emphasis rules

#### Scenario: Read progressively disclosed labels

- **WHEN** the learner changes zoom, search, hover, or focus
- **THEN** the corresponding ranked or explicitly relevant labels remain readable under the defined thresholds

#### Scenario: A long node label stays complete

- **WHEN** a knowledge-point title is longer than one label line
- **THEN** the label wraps to further lines and shows its full text without
  truncation or ellipsis, and collision spacing accounts for the wrapped
  extent

### Requirement: Graph detail is a learning dashboard

Selecting a graph node SHALL show only its readable title, concise action reminder, and one link to the formal knowledge-point page. Full evidence remains available to Agent context but SHALL NOT be repeated as student-facing graph parameters. The dashboard's colours SHALL agree with the selected node in the canvas: the indicator of the node's learning state SHALL use the same state colour the node carries under the active projection, and the formal-problem count the dashboard reports SHALL be the same count shown at the node centre. The dashboard SHALL NOT give a learning state a meaning that differs from the node's, and it SHALL remain the place where a node's learning state is named in words, so that removing state words from the node does not remove the state from the page.

#### Scenario: Node selection opens a concise dashboard

- **WHEN** a student selects a node
- **THEN** the right panel shows its name, any applicable `重点练习` or `可以复习` reminder, and one `打开知识点` link

#### Scenario: Node selection opens the dashboard

- **WHEN** a student selects a graph node
- **THEN** the same concise name, action reminder, and formal knowledge-point link are shown without implementation parameters

#### Scenario: The dashboard agrees with the node

- **WHEN** a student selects a node under the learning-state projection
- **THEN** the dashboard's learning-state indicator uses the same colour as that node's outer ring, and its formal-problem count matches the number shown at the node centre

### Requirement: Metric projection morphology

The knowledge graph page SHALL preserve the same visible node elements when the learner switches among relationship structure, formal-problem count, importance, and learning-state projections. A metric projection SHALL map higher values to a larger node radius, a thicker node outer ring, and a target nearer the canvas center, while retaining deterministic separation for equal values. Learning-state projection SHALL rank attention as `needs_work`, `review`, unmarked, then `mastered`. Each projection SHALL apply its own colour key — categorical colours for the relationship-structure and learning-state projections, and one hue in graded steps for the formal-problem-count and importance projections — without changing or persisting learning data. The graph SHALL NOT draw a progress arc or gauge around a node, so that node size and node colour are the only channels carrying a metric value. Under every projection the node centre SHALL show only the count of formal problems linked to that node, and SHALL NOT show a state word or a projection-specific value. Relationship edges SHALL be rendered only under the relationship-structure projection; metric projections SHALL render nodes only, without creating any relationship edge elements.

#### Scenario: Switch to a numeric metric

- **WHEN** the learner changes from relationship structure to formal-problem count
- **THEN** the same nodes move continuously toward deterministic metric targets and higher-count nodes become larger with a thicker outer ring and nearer the center, with no relationship edges created

#### Scenario: Read attention from learning state

- **WHEN** the learner selects learning-state projection
- **THEN** needs-work nodes are ranked above review, unmarked, and mastered nodes for size and radial position, with no relationship edges created

#### Scenario: Return to relationship structure

- **WHEN** the learner returns from a metric projection to relationship structure
- **THEN** the same nodes transition back toward a freshly computed relationship layout with relationship edges restored, without changing graph membership, selection, or stored coordinates

#### Scenario: Read one projection's colour key

- **WHEN** the learner switches among the relationship-structure, formal-problem-count, importance and learning-state projections
- **THEN** each projection's nodes take that projection's own colours — graded steps of one hue for the two magnitude projections and categorical colours for the relationship-structure and learning-state projections

#### Scenario: No gauge around a node

- **WHEN** any projection is active
- **THEN** no progress arc or gauge is drawn around a node, and the metric value is expressed by node size, outer-ring thickness and node colour only

### Requirement: Multi-state graph filtering

The knowledge graph SHALL expose a multi-select learning-state filter using exactly `needs_work`, `review`, `mastered`, and `null` as its values. No selected value SHALL mean no filtering. One or more selected values SHALL retain the union of matching nodes and only edges whose two endpoints remain visible. Filtering SHALL be independent of the active graph projection and SHALL NOT change the explicit practice selection or any learning data. Filtering SHALL change which nodes are shown, never how a node looks: a surviving node SHALL keep the graph's node appearance language and the colours of the active projection, and a node leaving the graph SHALL fade out rather than change its colour or shape. The filter SHALL NOT add any state source, state editor or per-node state marker beyond the node's own learning state.

#### Scenario: Show one state

- **WHEN** the learner selects only `review`
- **THEN** review nodes remain visible and all nonmatching nodes and incident edges fade out before leaving the active layout

#### Scenario: Show several states

- **WHEN** the learner selects `needs_work` and `mastered`
- **THEN** nodes from both categories and edges between visible endpoints remain in the graph

#### Scenario: Clear filtering

- **WHEN** the learner clears every selected state
- **THEN** all nodes and relationships reappear without changing the practice selection

#### Scenario: Filtering changes membership, not appearance

- **WHEN** the learner selects one or more learning states
- **THEN** the surviving nodes keep the same concentric form and the colours of the active projection, and the nodes leaving the graph fade out without changing colour

#### Scenario: Filtering adds no state channel

- **WHEN** the learner filters by learning state
- **THEN** no additional state marker, state word or state control appears on a node, and no learning record is written

### Requirement: Redundant state cues

<!-- ⚠️ A-10.2：须在 workbench-visual-language-v2 合入后 re-base 到 v2 的版本（见文件头）。本块正文目前是 v2 之前的基线文本，re-base 时删除本行标注。 -->

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain text, outline, position,
or another geometric cue in addition to color. On the knowledge graph page a
node's learning state SHALL be carried by the colour of its outer ring together
with the geometry of its concentric rings, and the state name SHALL remain
available as the node's accessible name and in the learning dashboard. No state
word SHALL be drawn on the node itself.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural inset

#### Scenario: Graph state

- **WHEN** a node has a formal learning state
- **THEN** its state name remains available as the node's accessible name and in
  the learning dashboard, its outer ring carries the state's colour together with
  the concentric geometry as the redundant cue, and no state word is drawn on the
  node

### Requirement: Soft Mondrian visual foundation

<!-- ⚠️ A-10.2：须在 workbench-visual-language-v2 合入后 re-base 到 v2 的版本（见文件头）。本块正文目前是 v2 之前的基线文本，re-base 时删除本行标注。 -->

The workbench SHALL use warm paper surfaces, dark structural rules, and restrained
blue, yellow, and red accents. Blue SHALL represent primary action and selection,
yellow SHALL represent current/review emphasis, and red SHALL represent needs-work
or failure emphasis. Most screen area SHALL remain paper or neutral. The
knowledge graph page is one explicit and scoped exception to the accent-role
quota: it is a data-visualisation area rather than an operating surface, so its
own colour keys — a warm magnitude hue, four learning-state colours and a
three-step ink scale — are not bound by the three accent roles above. The
graph's colours SHALL still come from the same paper-and-ink world, and SHALL
NOT claim an accent role for the workbench's operating surfaces.

#### Scenario: Ordinary workbench page

- **WHEN** a learner opens any core page
- **THEN** the shell is structured by paper surfaces and dark rules with only compact
  red, yellow, and blue accents

#### Scenario: Primary action

- **WHEN** a primary action is enabled
- **THEN** it is blue with a dark outline and remains identifiable by its label

#### Scenario: The graph keeps its own palette

- **WHEN** the learner opens the knowledge graph page
- **THEN** the graph's nodes and its legend use the graph's own colour keys, and those colours do not take over the blue, yellow and red accent roles used by the rest of the workbench
