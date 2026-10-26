## Purpose

The workbench UI is the minimal consumption surface of lesson-kit: a three-column
shell with a left navigation column (practice, knowledge points, knowledge
graph), a middle page area with Paper practice and optional self-rating, and a right AI
conversation column whose context display prioritizes the current problem
without ever limiting what the agent can see. Visual style follows the Soft
Mondrian visual foundation defined by this specification.
## Requirements
### Requirement: Three-column shell with navigation

The workbench SHALL render a three-column desktop layout: a left navigation column with workspace and study navigation, a primary middle page, and a collapsible right Agent conversation column, with the workspace name and the chapter lens in the top bar (the machine course identifier SHALL NOT be shown there). At narrow widths the middle page SHALL remain the single primary column; the left and right columns SHALL become dismissible drawers opened by two compact icon controls in the top bar. Switching workspaces or pages SHALL preserve recorded pool state.

#### Scenario: Navigate from the left column

- **WHEN** the learner clicks a navigation entry in the left column
- **THEN** the middle area shows the corresponding page for the current workspace

#### Scenario: Open mobile navigation

- **WHEN** a learner at a narrow viewport activates the navigation icon
- **THEN** the left column opens as a drawer without hiding the middle page permanently

#### Scenario: Open mobile Agent conversation

- **WHEN** a learner at a narrow viewport activates the conversation icon
- **THEN** the right column opens as a drawer and can be dismissed back to the middle page

#### Scenario: Switch workspace without losing state

- **WHEN** the learner switches the workspace dropdown
- **THEN** the new workspace loads and previously recorded attempts, feedback, and signals remain intact in their original pool

#### Scenario: The top bar shows the name, not the identifier

- **WHEN** a workspace's course is an automatically allocated code and its name is the folder name
- **THEN** the top bar shows the workspace name, and the code does not appear there

#### Scenario: The chapter context lives in the lens control

- **WHEN** a chapter is active
- **THEN** the top bar shows it through the chapter lens control rather than repeating it beside the workspace name

### Requirement: Practice page

The practice page SHALL list/manage existing Papers and offer start/continue, not learner-operated selection or assembly. It SHALL NOT expose per-problem pickers, knowledge-point assembly selectors, quantity/source/difficulty assembly controls, content-mode assembly inputs, suggestion-to-assembly actions, manual Paper membership/order edits, or a scope tray. Agent/CLI Paper Assembly and saving SHALL remain available. Reading, graph navigation and chapter-lens changes SHALL NOT select or assemble practice items. Existing Paper progress SHALL remain independent of these reading actions.

#### Scenario: Start from an explicit scope
- **WHEN** the learner asks the Agent to assemble from an explicit knowledge scope
- **THEN** the Agent authors/saves the fixed Paper and the page offers that saved Paper for practice without a learner scope-selection form

#### Scenario: Resume an active Paper
- **WHEN** the learner returns with an unfinished run
- **THEN** its Paper and progress are offered for continuation without assembly

#### Scenario: Filters do not mutate a running Paper
- **WHEN** Agent/CLI authoring filters or reading context change
- **THEN** the running Paper remains fixed and any authoring inputs apply only to a separately authored Paper

#### Scenario: No manual problem picker
- **WHEN** the learner visits practice, knowledge points, graph or saved-Paper surfaces
- **THEN** no learner action selects concrete questions, accumulates assembly scope, changes a Paper's item list/order or directly assembles a Paper

### Requirement: Knowledge point display page

The knowledge-point page SHALL render the body as its primary reading content and
provide one prominent `练习此知识点` action. Activating it SHALL transfer that
knowledge point as a Paper-assembly scope and open the practice departure flow;
it SHALL NOT directly create a dynamic, non-repeating Practice Session.

Linked formal problems SHALL remain reading-only and SHALL be listed directly
under the knowledge point with no stored topic/group layer. Each row SHALL show
`display_title` and the complete safe-rendered problem statement without summary
text, truncation, ellipsis, raw ids, or per-problem practice controls. Raw signal
and scheduler parameters SHALL not be shown.

#### Scenario: Practise one knowledge point

- **WHEN** a learner activates `练习此知识点`
- **THEN** practice opens with that knowledge point as the Paper-assembly scope and concrete items are chosen by assembly rather than by direct per-problem controls

#### Scenario: Browse linked problems directly

- **WHEN** a knowledge point has several linked formal problems
- **THEN** the page lists those problems directly without a synthetic topic/group heading or an independent practice button per problem

#### Scenario: Read a complete linked problem

- **WHEN** the learner opens a knowledge-point page with linked problems
- **THEN** each row shows the title and complete rendered statement without summary, truncation, raw id, or manual-add action

#### Scenario: Missing display title

- **WHEN** a linked problem lacks a display title
- **THEN** the row uses the fixed readable fallback `未命名题目` rather than a raw id or statement fragment

#### Scenario: Navigate a wiki link

- **WHEN** rendered knowledge content contains a valid workspace knowledge-point wiki link
- **THEN** activating it opens that formal knowledge-point route

#### Scenario: Hide implementation state

- **WHEN** the knowledge-point page contains signals or schedule data
- **THEN** it shows only the applicable concise action reminder and not raw signal, score, ease, repetition, scheduler, or mastery-state controls

### Requirement: Knowledge point list page

The knowledge point list and the left weak-point rail SHALL use each knowledge point’s readable name as primary text and show raw identifiers only as secondary context.

#### Scenario: Read weak points without decoding identifiers

- **WHEN** the learner views the weak-point rail
- **THEN** every entry is identifiable from its knowledge-point name without relying on its raw id

#### Scenario: Open the knowledge point list

- **WHEN** the learner clicks the knowledge point navigation entry
- **THEN** the middle area lists the chapter's knowledge points in weak order, each linking to its display page

### Requirement: Knowledge graph page

When browser Web Worker support, graph physics resources, and WebGL2 support are available, the knowledge graph page SHALL render the live complete chapter graph in a middle-column canvas that fills the viewport below its compact page tools. Six deterministic component layouts SHALL supply seed positions before every visible node enters one unbounded unified elastic field. Existing edge attraction SHALL determine variable semantic gaps from 72 to 144 pixels in addition to endpoint radii, and every pair of node circles SHALL retain at least 24 pixels of logical clearance. Relationship rendering SHALL preserve the existing physics-provided ports, lanes, bends, arrow direction, and endpoint clearance; DOM nodes SHALL remain the accessible and interactive source for node appearance, labels, selection, and drag input. The graph SHALL retain search, filter, zoom, pan, camera-only fit, drag, problem-count radius, focus, and the concise dashboard. Viewport culling and label/meta LOD SHALL affect paint only; for on-screen nodes, selected, hovered, and high-focus labels SHALL remain visible at reduced zoom, and graph membership and selection SHALL remain available. When browser `localStorage` is available, the graph runtime SHALL keep at most one optional settled local layout seed per workspace. Its readable identity SHALL contain the sorted node IDs and sorted relationship tuples of source, target, type, and direction. The graph SHALL read a seed only when its identity exactly matches the current graph, restore its coordinates as temporary anchors through the existing Worker, then release those anchors and reheat that same Worker. Filters, selection, motion, active anchors, authored content, and learning state SHALL NOT be restored from the seed. Missing, stale, corrupt, or unavailable storage SHALL leave the deterministic Worker startup unchanged. If Web Worker support, graph physics resources, WebGL2, or renderer initialization is unavailable, the page SHALL show a readable graph error; a renderer startup failure after Worker creation SHALL terminate that Worker and release partial renderer resources. The page SHALL NOT run the synchronous solver or fall back to SVG.

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

### Requirement: Free Agent conversation column

The right column SHALL provide free conversation on every workbench page without requiring a current problem. It SHALL show available providers, the current conversation, up to ten recent conversations, new conversation, successful messages and current turn events, an input, and a temporary stop control while running. Visible explain and diagnose shortcuts SHALL be removed while their existing APIs remain compatible.

#### Scenario: Start a free conversation

- **WHEN** the learner selects an available Agent and creates a conversation
- **THEN** the provider is locked for that conversation and the learner can send an ordinary message from the current page

#### Scenario: Restore a recent conversation

- **WHEN** the learner selects one of the workspace's ten recent conversations
- **THEN** its successful exchange mirror is rendered and later turns resume its provider-native session

#### Scenario: Stop a running turn

- **WHEN** a turn is running
- **THEN** send is disabled, a temporary stop control is visible, and cancellation reports its final state without switching provider

### Requirement: Authoritative page context for Agent turns

For each turn, the browser SHALL send object identifiers rather than the full
page DOM; the server SHALL rebuild authoritative workspace, course, chapter,
route, page type, selected object, and relevant learning context from SQLite.
Practice, knowledge-point, and graph pages SHALL retain their existing
object/state summaries and the latest three distinct browser-session anchors.
On the practice page, the current unsent answer text, selected options, note,
and currently displayed image references SHALL also be passed as bounded,
ephemeral learner input. They SHALL be treated as draft content, not database
facts, and SHALL NOT be written to the pool or conversation mirror merely by
sending a turn. Other pages keep their existing context behavior.

#### Scenario: Ask about a knowledge point page

- **WHEN** the learner sends a turn from a knowledge-point page
- **THEN** the Agent receives current content, evidence, schedule, neighbours, and related problems rebuilt from the workspace

#### Scenario: Keep a practice draft private

- **WHEN** an unsubmitted answer or note exists but no Agent turn or explicit practice submission occurs
- **THEN** it is absent from durable learning records and the conversation mirror

#### Scenario: Attach a practice draft explicitly

- **WHEN** a learner sends an Agent turn while a practice draft exists
- **THEN** the focused draft, chosen options, and visible image references are available to that turn without creating an attempt

#### Scenario: Agent reads the focused answer

- **WHEN** the learner is viewing an open problem with entered work and sends a chat message
- **THEN** the current problem and entered work take priority in Agent context while wider workspace reads remain available

### Requirement: User-visible Markdown uses one safe subset
All user-visible learning text SHALL use the same supported Markdown subset: ATX headings through level 3, paragraphs, ordered and unordered lists, blockquotes, thematic breaks, fenced and inline code, strong/emphasis, safe http(s) links, wiki links, math, and workspace-local images.

#### Scenario: Agent answer renders Markdown
- **WHEN** an Agent or student message contains `##`, `**bold**`, a list, or a fenced code block
- **THEN** the message displays semantic headings, emphasis, list markers, and code styling rather than raw Markdown syntax

#### Scenario: Markdown thematic break
- **WHEN** user-visible Markdown contains standalone `---`, `***`, or `___` outside a fenced code block
- **THEN** both browser and server renderers emit a semantic horizontal rule rather than showing the marker text
- **AND** the same markers inside a fenced code block remain literal code

#### Scenario: Unsafe markup is rejected
- **WHEN** text contains raw HTML, a `javascript:` link, or an image path outside the workspace figure directory
- **THEN** the rendered output contains escaped text and no executable link or image

### Requirement: Streaming text is one message
Partial Agent text events SHALL update one assistant message until the turn completes.

#### Scenario: Partial events coalesce
- **WHEN** a turn emits several text events
- **THEN** the UI shows one growing assistant message and renders the combined Markdown

### Requirement: The default Agent view is a session list
When the current tab has no open conversation, the Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require explicit available-provider selection, and provider ownership SHALL remain immutable. Rename/delete SHALL remain in compact history-row menus.

The chat view SHALL remain conversation-first: accessible icon return-to-list control, message stream, compact context chips and composer. Provider/session settings, daily-create controls and chat-page rename/delete SHALL NOT crowd that view. The client SHALL NOT revive provider-memory/daily-create keys or the removed explain/diagnose console. Same-workspace middle navigation SHALL NOT initialize the rail again.

#### Scenario: Chat is quiet
- **WHEN** the learner opens an existing conversation
- **THEN** the rail presents conversation, compact context and currently relevant message controls without unrelated settings or task dashboards

#### Scenario: History is the first view
- **WHEN** a workbench page opens with no conversation selected in the current tab
- **THEN** the rail shows the session list and no conversation is opened or created

#### Scenario: Return to history
- **WHEN** the learner explicitly uses the back icon
- **THEN** history returns without creating a session or learning record

#### Scenario: History row actions
- **WHEN** the learner chooses rename/delete from a history-row menu
- **THEN** the corresponding local mirror action runs and those controls remain absent from chat view

### Requirement: Agent rail keeps the open conversation across page navigation
Within the same workspace, switching the central view, its query state or browser back/forward SHALL keep the Agent rail instance and its selected conversation, draft/caret/focus, scroll position and current streaming/polling state intact. It SHALL NOT transiently return to the list, destroy/recreate the rail or rebuild conversation history merely to navigate the middle page. Current-page context chips SHALL update.

A full same-tab reload SHALL restore the selected conversation. Returning to the list SHALL require explicit learner action. A confirmed missing conversation SHALL fall back to the list without an error wall or creating a conversation. Other read errors SHALL retain the selection and show recoverable feedback. Workspace boundaries SHALL retain their existing isolation.

#### Scenario: Switch the central view
- **WHEN** a conversation is open and the learner navigates between practice, Papers, KP detail, graph or records in the same workspace
- **THEN** the existing rail DOM/controller remains mounted with draft/scroll/stream intact, no list is shown and only middle-owned resources are replaced

#### Scenario: Reload the page
- **WHEN** the learner fully reloads the workspace in the same tab
- **THEN** the selected conversation is restored without creating another session

#### Scenario: Return to the list explicitly
- **WHEN** the learner uses the return-to-list control
- **THEN** the list returns and later middle navigation/reload preserves that explicit selection state

#### Scenario: The open conversation disappears
- **WHEN** the selected conversation is confirmed missing in the workspace
- **THEN** the rail shows the list without an error wall and creates no conversation

#### Scenario: Restoring the open conversation temporarily fails
- **WHEN** a conversation read fails without confirmed deletion
- **THEN** the selection and recoverable message text are retained and the UI offers a recoverable error rather than discarding the conversation

#### Scenario: Navigate back while an answer streams
- **WHEN** the user changes the middle route and then uses browser Back during streaming
- **THEN** only the middle route changes; the same turn/poll ownership, unsent draft and deliberate scroll position survive

Activity progress surfaces, Float collapse/reopen behavior, idle cleanup, and Bottom Dock retirement are specified only in the independent `use-collapsible-agent-activity-float` change.

### Requirement: Provider is selected once
New-session flow SHALL require an explicit available provider choice before creation. A created session SHALL display its provider as read-only.

#### Scenario: Provider is locked after creation
- **WHEN** a student creates a session with Codex
- **THEN** the conversation view shows Codex without a provider switch control

### Requirement: Session title is explicit
The mirror SHALL store `title` and `title_source`. A successful provider result MAY supply a title only when the session is unset; an explicit user rename SHALL take precedence.

#### Scenario: User title wins
- **WHEN** a student renames a session after an Agent title was received
- **THEN** later turns do not replace the user title

### Requirement: Local deletion is bounded
Deleting an idle session SHALL remove only its Lesson Kit mirror directory. A running session SHALL return a conflict and remain intact. The identifier SHALL be validated as a plain generated conversation name before any filesystem call, so a request that carries a path separator or `..` is refused with an explicit error and removes nothing.

#### Scenario: Returning to history
- **WHEN** a student clicks back from a conversation
- **THEN** the list view returns without creating or modifying a learning record

#### Scenario: A traversal identifier is refused
- **WHEN** a delete or rename request carries a conversation identifier that is not a plain name
- **THEN** the request fails with an explicit error and no directory inside or outside the workspace is removed

#### Scenario: Another workspace's conversation is unreachable
- **WHEN** a delete request names a conversation that belongs to a different workspace
- **THEN** the request fails as unknown and the other workspace's jobs directory is untouched

### Requirement: Graph detail is a learning dashboard

Selecting a graph node SHALL show only its readable title, concise action reminder, and one link to the formal knowledge-point page. Full evidence remains available to Agent context but SHALL NOT be repeated as student-facing graph parameters.

#### Scenario: Node selection opens a concise dashboard

- **WHEN** a student selects a node
- **THEN** the right panel shows its name, any applicable `重点练习` or `可以复习` reminder, and one `打开知识点` link

#### Scenario: Node selection opens the dashboard

- **WHEN** a student selects a graph node
- **THEN** the same concise name, action reminder, and formal knowledge-point link are shown without implementation parameters

### Requirement: Graph state editing remains covered

The existing graph-state compatibility API SHALL remain available, but the student graph dashboard SHALL NOT expose a manual `needs_work`, `review`, or `mastered` editor.

#### Scenario: Browse without manual state controls

- **WHEN** a student opens a selected node dashboard
- **THEN** no mastery-state selector or save control is rendered and no state write occurs

#### Scenario: State update is coverage based

- **WHEN** an existing client invokes the compatible graph-state API explicitly
- **THEN** its existing coverage-based state and schedule behavior remains compatible while the current student dashboard offers no such control

### Requirement: Graph does not duplicate content editing
The graph panel SHALL NOT render knowledge-point body textareas, fragile-note editors, complete linked-problem content, or per-problem save controls.

#### Scenario: Deep reading uses the formal page
- **WHEN** a student needs the full body or linked problem text
- **THEN** the graph panel offers the formal knowledge-point link instead of duplicate editors

### Requirement: Visible local failure states

Practice pull, solution reveal, rating save, and Agent-provider failures SHALL appear inside the currently visible page, picker, or chat state that initiated the request. A failure SHALL NOT leave the learner with only a hidden status message or a blank primary region.

#### Scenario: No Agent provider is available

- **WHEN** the learner opens the visible new-conversation provider picker and no provider is available
- **THEN** that picker explains the unavailable state without creating a session

#### Scenario: Practice request fails

- **WHEN** a practice request fails
- **THEN** the current practice region presents the error and an available next action

### Requirement: Dynamic practice controls are accessible

Repeated unified-rating controls SHALL use unique identifiers, associated accessible labels, and titled problem cards. Raw problem ids MAY remain in data attributes for requests but SHALL NOT be the card's primary text.

#### Scenario: Review several pending cards

- **WHEN** multiple unified-rating cards are rendered
- **THEN** every rating and note control has a unique id and an accessible name associated with its display title

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

### Requirement: Adjustable graph compactness

The existing 0–100 in-memory center-gravity control SHALL provide a visibly stronger range, with a maximum coefficient of approximately `0.00351` and default value 30. Higher values SHALL draw all nodes more toward the graph center and lower values SHALL let them spread, regardless of whether nodes have connecting edges. The value SHALL NOT be persisted or written to learning records.

#### Scenario: Increase graph gravity

- **WHEN** the learner raises the gravity control
- **THEN** the current simulation reheats with a stronger center force and the graph remains otherwise unchanged

#### Scenario: Lower graph gravity

- **WHEN** the learner lowers the gravity control
- **THEN** the current simulation reheats with a weaker center force and unconnected nodes may spread farther apart

### Requirement: Resizable desktop sidebars

The desktop workbench SHALL expose pointer-drag handles on the inner edges of the left and right columns. Dragging SHALL adjust only the current page's in-memory grid widths within readable bounds; mobile drawer behavior and all learning data SHALL remain unchanged.

#### Scenario: Resize sidebars

- **WHEN** the learner drags a sidebar edge on a desktop viewport
- **THEN** the corresponding column width changes within its bounds without navigation or persistence

### Requirement: Scrollable Agent conversation

The Agent chat SHALL constrain its message region to the available column height and allow normal mouse-wheel vertical scrolling when messages exceed that height.

#### Scenario: Read long conversation

- **WHEN** the Agent message list is taller than the visible right column
- **THEN** the learner can scroll the message region with the mouse wheel while the input remains available

### Requirement: Fixed outer sidebar boundaries

On desktop, resizing either sidebar SHALL change only that sidebar and the flexible middle column. The left outer edge SHALL remain at the viewport left, the right outer edge SHALL remain at the viewport right, and the middle column SHALL retain at least 420px.

#### Scenario: Expand either sidebar

- **WHEN** the learner drags a sidebar edge
- **THEN** only the middle column yields space, the opposite sidebar remains visible, and the layout does not overflow

### Requirement: Chat view owns the right-column height

In chat state, the complete session-controls region SHALL be removed from layout. The compact chat header, scrollable messages, and input row SHALL fill the right column.

#### Scenario: Open a conversation

- **WHEN** the learner opens or creates a conversation
- **THEN** the session controls reserve no space above the chat

### Requirement: Knowledge view sorting

The list view SHALL default to course/chapter source order and SHALL provide
stable ascending and descending sorting for each exposed computed column. The
graph SHALL default to relationship layout and SHALL expose only projections
based on existing data.

#### Scenario: Toggle sort
- **WHEN** the learner activates the same sort key repeatedly
- **THEN** order alternates ascending, descending, ascending without changing
  selection or writing a learning record

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

### Requirement: Metric projection morphology

The knowledge graph page SHALL preserve the same visible node elements when the learner switches among relationship structure, formal-problem count, importance, and learning-state projections. A metric projection SHALL map higher values to both a larger node radius and a target nearer the canvas center, while retaining deterministic separation for equal values. Learning-state projection SHALL rank attention as `needs_work`, `review`, unmarked, then `mastered`. Each projection SHALL apply a restrained, distinguishable Mondrian palette without changing or persisting learning data. Relationship edges SHALL be rendered only under the relationship-structure projection; metric projections SHALL render nodes only, without creating any relationship edge elements.

#### Scenario: Switch to a numeric metric

- **WHEN** the learner changes from relationship structure to formal-problem count
- **THEN** the same nodes move continuously toward deterministic metric targets and higher-count nodes become larger and nearer the center, with no relationship edges created

#### Scenario: Read attention from learning state

- **WHEN** the learner selects learning-state projection
- **THEN** needs-work nodes are ranked above review, unmarked, and mastered nodes for size and radial position, with no relationship edges created

#### Scenario: Return to relationship structure

- **WHEN** the learner returns from a metric projection to relationship structure
- **THEN** the same nodes transition back toward a freshly computed relationship layout with relationship edges restored, without changing graph membership, selection, or stored coordinates

### Requirement: Metric projection transition

Projection changes SHALL reheat the existing in-memory simulation and animate node position and radius toward their new targets with bounded velocity, so nodes appear to bubble inward or outward rather than teleport. A settled projection SHALL become fully static. When reduced motion is requested, the graph SHALL compute and draw the stable projected result synchronously without scheduling animation frames.

#### Scenario: Metric transition settles

- **WHEN** an ordinary-motion learner changes the active graph projection
- **THEN** nodes move together until the new projection settles and no recurring animation remains

#### Scenario: Reduced-motion metric switch

- **WHEN** a reduced-motion learner changes the active graph projection
- **THEN** the projected terminal layout is drawn without requesting animation frames

### Requirement: Multi-state graph filtering

The knowledge graph SHALL expose a multi-select learning-state filter using exactly `needs_work`, `review`, `mastered`, and `null` as its values. No selected value SHALL mean no filtering. One or more selected values SHALL retain the union of matching nodes and only edges whose two endpoints remain visible. Filtering SHALL be independent of the active graph projection and SHALL NOT change the explicit practice selection or any learning data.

#### Scenario: Show one state

- **WHEN** the learner selects only `review`
- **THEN** review nodes remain visible and all nonmatching nodes and incident edges fade out before leaving the active layout

#### Scenario: Show several states

- **WHEN** the learner selects `needs_work` and `mastered`
- **THEN** nodes from both categories and edges between visible endpoints remain in the graph

#### Scenario: Clear filtering

- **WHEN** the learner clears every selected state
- **THEN** all nodes and relationships reappear without changing the practice selection

### Requirement: State cluster layout

When state filtering is active, each visible state SHALL receive a deterministic cluster center. Nodes SHALL move through the existing bounded-velocity force simulation toward their state's center, so one selected category forms one group and multiple selected categories form separate groups. Cross-category edges MAY remain visible but SHALL exert reduced pull so the groups stay distinguishable. Reduced-motion mode SHALL draw the stable filtered layout without transition frames.

#### Scenario: One selected category forms one group

- **WHEN** exactly one state is selected
- **THEN** its visible nodes gather around one central cluster target

#### Scenario: Several selected categories form separate groups

- **WHEN** two or more states are selected
- **THEN** each state gathers around a separate deterministic center while visible relationships remain attached

#### Scenario: Reduced-motion filtering

- **WHEN** a reduced-motion learner changes the state filter
- **THEN** the graph draws the stable filtered clusters without scheduling fade or movement frames

### Requirement: Layered knowledge relationships

The structure projection SHALL draw each visible relationship as a layered pipe
consisting of a soft shadow, a body, and a narrow highlight. Existing attraction
strength SHALL monotonically control body width and darkness. Weak relationships
SHALL be drawn before strong relationships so strong evidence remains visually
prominent. These visual channels SHALL NOT alter relationship data or learning state.

#### Scenario: Compare weak and strong relationships

- **WHEN** two visible relationships have different attraction strength
- **THEN** the stronger relationship is wider, darker, and drawn above the weaker one

#### Scenario: Relationship remains attached during motion

- **WHEN** connected nodes move through the force simulation
- **THEN** all three layers follow the same straight or curved path

### Requirement: Finite crossing optimization

Each deterministic candidate layout SHALL receive a finite deterministic position-swap
pass before candidates are compared. A swap SHALL be retained only when it improves
the lexicographic layout score: crossings, label collisions, total edge length, then
occupied area. The optimization SHALL schedule no recurring background work.

#### Scenario: Avoidable crossing

- **WHEN** swapping two node positions reduces the crossing count
- **THEN** the improved positions are retained

#### Scenario: Stable result

- **WHEN** the same graph and canvas dimensions are laid out twice
- **THEN** the selected positions and relationship ordering are identical

### Requirement: Complete primary learning text

The workbench SHALL display user-authored knowledge titles, questions, notes, goal
titles, and practice-scope titles in full. These primary labels SHALL wrap within
their available column and SHALL NOT use ellipsis. Flex and grid containers around
them SHALL allow content children to shrink without widening the three-column shell.

#### Scenario: Long unbroken title

- **WHEN** a primary title contains a string wider than its column
- **THEN** it wraps inside the column without clipping or widening the page

#### Scenario: Practice scope title

- **WHEN** a selected or suggested knowledge title spans several lines
- **THEN** every character remains visible and adjacent controls remain usable

### Requirement: Locally scroll wide artifacts

Code blocks, display mathematics, and tables SHALL remain complete and SHALL scroll
horizontally inside their own rendered surface when wider than the available column.
Long inline-code tokens SHALL wrap. None of these artifacts SHALL widen the middle
page or Agent column.

#### Scenario: Wide code block

- **WHEN** a code line is wider than the content column
- **THEN** the code surface scrolls horizontally while the page width stays fixed

#### Scenario: Wide table in Agent output

- **WHEN** an Agent message contains a table wider than the right column
- **THEN** the table scrolls locally and the conversation composer remains in view

### Requirement: Soft Mondrian visual foundation

The workbench SHALL use warm paper surfaces, dark structural rules, and restrained
blue, yellow, and red accents. Blue SHALL represent primary action and selection,
yellow SHALL represent current/review emphasis, and red SHALL represent needs-work
or failure emphasis. Most screen area SHALL remain paper or neutral.

#### Scenario: Ordinary workbench page

- **WHEN** a learner opens any core page
- **THEN** the shell is structured by paper surfaces and dark rules with only compact
  red, yellow, and blue accents

#### Scenario: Primary action

- **WHEN** a primary action is enabled
- **THEN** it is blue with a dark outline and remains identifiable by its label

### Requirement: Redundant state cues

Color SHALL NOT be the only carrier of learning or interaction state. Active
navigation, graph learning states, and errors SHALL retain text, outline, position,
or another geometric cue in addition to color.

#### Scenario: Active navigation

- **WHEN** a navigation item is active
- **THEN** it has both active text styling and a blue structural inset

#### Scenario: Graph state

- **WHEN** a node has a formal learning state
- **THEN** its existing state name remains available while its outline uses the
  corresponding visual role

### Requirement: Learning content is the visual anchor

An active practice question and a knowledge-point body SHALL use the primary reading
rhythm of at least 17px text with generous line height. Each SHALL use one structural
accent edge and SHALL avoid decorative shadow emphasis. Controls and metadata SHALL
remain visually secondary.

#### Scenario: Active question

- **WHEN** a practice item is shown
- **THEN** the question text is the strongest surface and the answer composer follows
  as a distinct action area

#### Scenario: Knowledge body

- **WHEN** a knowledge point is opened
- **THEN** its prose forms the primary reading surface before reminders and related
  problems

### Requirement: Supporting learning surfaces remain quiet

Mode selection, revealed solutions, and related-problem navigation SHALL use secondary
backgrounds, text, or spacing. They SHALL NOT add another competing primary action or
change the current practice choreography.

#### Scenario: Reveal solution

- **WHEN** a learner reveals a solution
- **THEN** it appears attached beneath the question with secondary text styling

#### Scenario: Browse related problems

- **WHEN** a learner reaches the related-problem section
- **THEN** the section is separated from the knowledge body and linked problems remain a direct, quiet list

### Requirement: Flash card item stacked presentation

A flash-card item inside a Paper SHALL render as two fully overlapped card faces:
the prompt face on top and the other face hidden behind it until the explicit
reveal action. Revealing SHALL preserve the current stacked-card motion and
reduced-motion terminal state.

Direction is item/assembly metadata, not a separate executable Practice Session.
A card-only compatibility flow MAY apply one forward/reverse preference to all
cards when assembling its Paper; once a card item is in a running Paper, its
direction SHALL remain fixed for that item and no swap control SHALL mutate it in
place.

#### Scenario: Reveal the hidden face

- **WHEN** the learner activates reveal on an unrevealed flash-card item
- **THEN** the prompt and answer faces reach the existing readable revealed presentation

#### Scenario: Direction is fixed after Paper assembly

- **WHEN** a flash-card item enters a Practice Run with reverse direction
- **THEN** that item prompts from the back and its direction does not change during the run

#### Scenario: Reduced motion reveal

- **WHEN** reduced motion is requested and the learner reveals a card
- **THEN** both faces are shown in their final positions without animation frames

### Requirement: Chapter switch in the top bar

The workbench top bar SHALL carry one chapter control beside the workspace and
course context: a switch whose off state means the whole course and whose on
state selects exactly one chapter from the chapters present in the pool. The
control SHALL write the active chapter through the service and refresh the
shell, SHALL NOT introduce a fourth navigation page, and SHALL show no
per-chapter statistics, counts, or selection reasons.

#### Scenario: Toggle the lens on

- **WHEN** the learner turns the chapter switch on and selects a chapter
- **THEN** the shell reloads with that chapter's context and the control shows the selected chapter

#### Scenario: Toggle the lens off

- **WHEN** the learner turns the chapter switch off
- **THEN** the shell reloads with the whole-course context and the control shows no chapter

#### Scenario: No new navigation surface

- **WHEN** the chapter control is used
- **THEN** the three-page shell and its navigation entries remain unchanged

### Requirement: Pi activities are conversation messages

The chat SHALL render each Pi concrete activity as an independent compact
message in event order. Updates with the same activity id SHALL update that
message in place. Tool output SHALL be collapsed by default. Codex and Claude
SHALL continue using the existing execution-plan presentation.

#### Scenario: Pi command completes

- **WHEN** a Pi command activity changes from running to done
- **THEN** one compact message changes state without adding a duplicate row

#### Scenario: Output is present

- **WHEN** a Pi activity carries command or tool output
- **THEN** the output is available behind a closed disclosure for running, done, and failed states

### Requirement: Pi text follows event chronology

Contiguous Pi text deltas SHALL grow one assistant bubble. A concrete activity
after text SHALL close that segment; later text SHALL start a new bubble after
the activity. The durable successful mirror may restore the coalesced activities
before the final combined answer.

#### Scenario: Tool call interrupts text

- **WHEN** Pi emits text, then a tool activity, then more text
- **THEN** the chat shows text bubble, activity message, and a new text bubble in that order

### Requirement: Rich-text surfaces share one safe feature set

Agent messages and server-rendered linked-problem text SHALL both support
headings, ordered/unordered lists, blockquotes, thematic breaks, emphasis, code,
links, images, inline/display math, and GFM tables. Table cells SHALL use the
same escaping and inline rules, and tables SHALL scroll locally on narrow
surfaces. Raw HTML SHALL remain escaped/rejected.

#### Scenario: Pi answers with a table

- **WHEN** a Pi answer contains a Markdown header row, delimiter row, and body rows
- **THEN** the conversation renders a table rather than literal pipe text

#### Scenario: Linked problem contains rich content

- **WHEN** a linked problem contains table, math, and image Markdown
- **THEN** the knowledge-point row renders all three with the same safe semantics

### Requirement: Content results expose type, source, and rollback state

An automatically executed append action SHALL render a result card containing
the final asset types/counts, affected workspace, source summary, figure count,
batch id, backup, and current rollback state. Formal/linked problems SHALL show
concise source evidence. Solution reveal SHALL preserve source answers and useful
normal explanations without a standalone `AI 生成解析` panel. Identical detailed
solution text already shown as the answer or quiz explanation SHALL appear once.
Stored solution content and provenance SHALL NOT be deleted by this presentation change.

#### Scenario: Source problem enters automatically
- **WHEN** an Agent action imports formal source problems
- **THEN** the result card states that type and every rendered problem shows its source evidence

#### Scenario: Reopen a rolled-back result
- **WHEN** a conversation is reopened after its batch was rolled back
- **THEN** the card shows `已回滚` and exposes no rollback button

#### Scenario: Generated explanation repeats the normal explanation
- **WHEN** detailed solution text repeats the displayed quiz explanation or source answer
- **THEN** the text is not repeated in another panel, no standalone AI explanation label appears, and stored fields remain intact

### Requirement: Failed activities expose a concise error summary

A failed activity SHALL display a sanitized error summary of at most 240
characters without requiring expansion. Full bounded tool output SHALL remain
collapsed by default. Empty output SHALL produce an explicit generic failure
message. Existing sensitive-value redaction SHALL precede truncation/storage.

#### Scenario: Pi tool reports an error

- **WHEN** Pi emits tool_execution_end with isError=true and diagnostic text
- **THEN** the activity visibly shows failure and its short diagnostic while full output remains collapsed

#### Scenario: Error output is empty

- **WHEN** a tool fails without diagnostic text
- **THEN** the activity shows a generic failure summary rather than a blank detail

#### Scenario: Failure contains sensitive and long output

- **WHEN** a failed activity contains secrets and more than 240 characters
- **THEN** its summary is redacted and bounded and cannot expose the removed sensitive values

### Requirement: Records center

The three-column shell SHALL expose a 记录 navigation entry as a dedicated
server-rendered history center. It SHALL provide overview, practice/paper runs,
attempt details, and wrong/stuck views. Attempt rows SHALL retain the linked
problem, honest verdict (对 / 错 / 未判定), linked rating, note, answer excerpt,
and time. Overview statistics and charts SHALL be derived from durable attempts
and feedback at read time and SHALL NOT write cached statistics.

A completed or explicitly replaced/cleared active practice SHALL leave one
minimal durable run snapshot containing its source kind/reference/label,
practice/rating modes, item order/final states, and timestamps. A saved paper
run SHALL therefore remain identifiable as that paper without copying problem
text, solutions, ratings, or other learning evidence into the run snapshot.

#### Scenario: A fresh workspace shows an honest empty state

- **WHEN** no attempt or archived run exists in the pool
- **THEN** the records center shows zero/empty views instead of fabricated activity

#### Scenario: A saved paper is completed

- **WHEN** an active practice started from a saved paper finishes
- **THEN** the run view shows one completed paper run with its saved title and item progress while the attempts remain the per-problem evidence

#### Scenario: Overview is read-only

- **WHEN** the records overview renders its 14-day volume, accuracy, and rating distribution
- **THEN** those values are aggregated from existing records and no learning or statistics row is written

#### Scenario: One problem's history is isolatable

- **WHEN** the records page is opened with a problem identifier
- **THEN** only that problem's attempts and attempt-derived statistics are shown

### Requirement: Problem fields render math wherever they render text

Every surface that renders a problem field as rich text SHALL run the same
math pipeline over it — including objective-item options and the live verdict
line's error reason, which previously escaped (or worse, concatenated) their
text. A field rendered escaped-only elsewhere SHALL NOT appear rendered in one
place and raw in another on the same screen.

#### Scenario: Options render their math

- **WHEN** a choice item's option text contains `$…$` math
- **THEN** the option label renders the formula with KaTeX, the same string the reveal renders

#### Scenario: The verdict line is safe and rendered

- **WHEN** an objective answer is graded wrong and the error reason carries math or markup
- **THEN** the reason is escaped-then-rendered, never injected raw

### Requirement: In-chat model switcher

The chat header SHALL offer a model select listing the model entries of the
conversation's own harness, marking the conversation's current model; choosing
one switches the conversation's model for the next turn and is reflected on
reload. Switching SHALL be refused while a turn is running, and a raw model id
no entry names SHALL be shown as the current choice so the state is never
silent.

#### Scenario: The switcher reflects and changes the model

- **WHEN** a conversation is opened and the learner picks another entry
- **THEN** the conversation records the new model, the next turn runs on it, and reloading shows the new selection

### Requirement: Saved paper items preview their problem

The saved-Paper page SHALL allow reading each item's full text and source in a collapsed-by-default expandable block using the shared safe Markdown subset, including math, figures and code. Summaries SHALL show index and title without reorder/remove controls. Preview SHALL change no Paper or practice state.

#### Scenario: Read one problem of a saved paper
- **WHEN** an item is expanded
- **THEN** its text and recorded source appear without leaving the page

#### Scenario: A long paper stays scannable
- **WHEN** a Paper contains many items
- **THEN** items arrive collapsed with visible disclosure controls

#### Scenario: Preview does not disturb the paper
- **WHEN** items are expanded or collapsed
- **THEN** membership, order and execution state remain unchanged, and no learner reorder/remove controls appear

### Requirement: Saved paper cards fold

Saved Paper cards SHALL arrive folded with title, count and management controls visible. Learners SHALL retain preview, rename, export, container deletion and start/continue as applicable, without membership/order editing. Fold state SHALL be reading-only, persist within the tab across management refreshes, and not change because a head control is activated. Errors SHALL remain visible on folded cards.

#### Scenario: A folded card shows its head only
- **WHEN** the saved-Paper page renders
- **THEN** title, count and management controls remain visible while items fold away

#### Scenario: An edit leaves the paper open
- **WHEN** a learner renames an open Paper and its management view refreshes
- **THEN** the card remains open in that tab

#### Scenario: A control does not fold the card
- **WHEN** rename or start/continue is activated
- **THEN** the action runs without toggling the card

#### Scenario: An error remains visible on a folded card
- **WHEN** rename or export fails on a folded card
- **THEN** its readable error remains visible outside the item list

### Requirement: Learner settings in the left rail

The workbench's left column SHALL carry a settings section whose preferences
apply across the practice and paper surfaces. Its first preference SHALL be a
checkbox, 「练习与试卷显示自评」, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭自评. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL immediately hide or show eligible self-rating controls in an open ordinary Paper, including a Paper started with rating off. Answer locking, navigation, objective grading and the recorded round mode SHALL remain unchanged. Legacy card/session timing retains its existing round mode.

#### Scenario: The preference survives a restart

- **WHEN** the learner turns the checkbox off and reopens the workbench later
- **THEN** the checkbox is still off and a new round starts without any
  self-rating surface

#### Scenario: Off removes every rating surface

- **WHEN** a round starts with the preference off
- **THEN** the rating-timing fieldset is absent, no feedback panel appears
  during the round, the round ends without the session-end view, and records
  show 关闭自评 for it

#### Scenario: On keeps today's behavior

- **WHEN** the preference is on
- **THEN** the rating-timing choice, per-problem rating, and session-end
  unified rating behave as before

#### Scenario: Reenable optional self-rating during a Paper

- **WHEN** an ordinary Paper started with self-rating off and the learner turns the display preference on after submitting an eligible item
- **THEN** the existing item offers optional self-rating without restarting, duplicating an Attempt or changing its answer lock

### Requirement: Long provider lists remain navigable
At desktop widths, when the visible new-conversation provider picker has more model options than fit in the available height, the system SHALL allow the learner to scroll the options with native wheel input while keeping the picker heading and helper text visible.

#### Scenario: Scroll a long provider list
- **WHEN** the learner opens the provider picker with a long model list and wheels up or down over the options at desktop width
- **THEN** the options move in the requested direction while the picker heading and helper text remain visible

### Requirement: Agent rail presentation keeps the learning page primary

The Agent rail SHALL remain a conversation surface within the existing workbench shell, and the current Lesson Kit page SHALL remain the primary learning surface. The rail SHALL show compact chips for the current page and available page context without changing the context sent to the provider. Its text composer SHALL grow to fit entered text within the rail. Agent presentation SHALL reuse the existing workbench visual tokens; an idle rail SHALL NOT leave an auxiliary work surface open.

#### Scenario: Read the current Agent context

- **WHEN** the learner opens an Agent conversation on a workbench page
- **THEN** the rail shows the current page and available page context as compact chips while the current Lesson Kit page remains visible

#### Scenario: Enter a longer message

- **WHEN** the learner enters multiple lines in the Agent composer
- **THEN** the composer grows to show the entered text without replacing the conversation with a task dashboard

#### Scenario: No runtime activity is present

- **WHEN** the Agent is idle and no Artifact preview is active
- **THEN** the central page remains unobstructed by an Activity Float or Bottom Dock

### Requirement: Agent runtime work uses transient auxiliary surfaces

Short and sustained provider activity SHALL use only the top-right replaceable
Activity Float for progress and current milestones. A Bottom Dock SHALL NOT
open or reserve middle-page height during work. The Float SHALL remain bounded
and SHALL NOT become a history dashboard or raw event wall. Existing
conversation activity/history SHALL remain authoritative.

#### Scenario: A short activity is visible

- **WHEN** a provider reports a short activity
- **THEN** the Activity Float shows its readable label and current state, and a
  later short activity replaces that float content

#### Scenario: Work continues across milestones

- **WHEN** a provider reports sustained multi-step work
- **THEN** the same top-right Activity Float summarizes current milestones and
  latest status while the middle page keeps its height and no Bottom Dock opens

#### Scenario: Detailed output is available

- **WHEN** an activity includes provider output
- **THEN** the transient surface keeps the semantic summary visible and the
  detailed output remains behind the existing closed disclosure in the
  conversation

#### Scenario: A provider confirms a failure

- **WHEN** the provider reports that the current turn failed
- **THEN** the work surface shows a concise failure summary and retains detailed
  output behind the existing closed disclosure

#### Scenario: Progress cannot be read

- **WHEN** a progress request fails while the provider turn has no authoritative
  terminal status
- **THEN** the interface reports that progress is unavailable, keeps the
  current turn gated against another send, and does not label the provider turn
  as failed

### Requirement: Explicit collapse applies to the current Agent turn

A small keyboard-accessible control SHALL expand or collapse the Activity
Float with a truthful label and `aria-expanded`. Collapsing SHALL leave a
compact reopening control while runtime progress is available. Later activity
updates in the same user turn SHALL NOT automatically reopen the Float;
explicit expansion MAY reopen it. A new user turn SHALL reset this suppression.
Switching conversations SHALL clear the prior conversation's transient
surfaces and collapse state. Idle SHALL NOT leave an empty Float or placeholder
panel.

#### Scenario: Collapse while work is running

- **WHEN** the learner collapses the Activity Float during a user turn and
  another activity arrives
- **THEN** the new activity remains in the conversation history, the Float
  stays closed and the small reopening control remains available

#### Scenario: Start a later user turn

- **WHEN** the learner sends a new message after the previous turn has ended
- **THEN** automatic Activity Float presentation is enabled for the new turn

#### Scenario: Switch conversations

- **WHEN** the learner opens a different conversation
- **THEN** no activity surface or collapse state from the previous conversation
  appears in the new one

#### Scenario: Reopen the current Float explicitly

- **WHEN** the learner activates the collapsed Float's small control
- **THEN** current progress reopens without changing the selected middle page or
  starting another task

#### Scenario: No runtime activity remains

- **WHEN** the current Agent turn has ended and no activity remains
- **THEN** the Activity Float and its reopening control are removed

### Requirement: Agent sending is single-flight and session-bound

The Agent text composer SHALL remain editable while a turn is active. The send
action SHALL be gated only while that submission's network acceptance request
is in flight; after acceptance, later distinct messages MAY be submitted to
the same conversation's queue or explicit interrupt-and-send path. Click and
Enter SHALL share the per-request gate, including while the initial request is
awaiting its accepted turn identifier. Accepting a queued message SHALL NOT
replace the currently running turn, clear its streaming state, or reset its
activity surface. A conversation change SHALL invalidate pending approvals,
activities, polling position, and callbacks owned by the previous conversation.
Late responses from the previous conversation SHALL NOT update or act on the
newly selected conversation.

#### Scenario: Type during a running turn

- **WHEN** an Agent turn is active and the learner sends another message
- **THEN** the composer remains usable and the configured queue or explicit interrupt action is applied without starting a concurrent provider

#### Scenario: Submit twice before receiving a turn identifier

- **WHEN** the learner activates Send and then presses Enter before the first send request returns
- **THEN** only one turn-creation request is sent

#### Scenario: Accept a queued message while a turn streams

- **WHEN** a queued message is accepted while another turn is streaming
- **THEN** the active turn identity, streamed content, polling position, and Activity Float remain intact

#### Scenario: Switch sessions with pending runtime state

- **WHEN** the learner switches conversations while an activity, progress request, or approval is pending
- **THEN** the old state is cleared and any late callback is ignored without mutating or sending an action for the new conversation

#### Scenario: Progress polling fails before a terminal response

- **WHEN** the progress endpoint is temporarily unavailable while a turn is active
- **THEN** the interface keeps the active turn identity, reports unavailable progress, and does not treat the provider as failed or start a concurrent turn

### Requirement: Low-reversibility rollback requires an Approval Gate

A content-batch rollback initiated from an Agent result card SHALL require an Approval Gate before the existing rollback operation is called. The gate SHALL identify the batch, explain the reason and impact, and replace the normal composer until the learner approves or cancels. Approval SHALL call the existing rollback operation once. Cancellation SHALL restore the composer without issuing a rollback request. Ordinary reversible provider activity SHALL NOT use this gate. A conversation change SHALL invalidate any approval callback from the prior conversation.

#### Scenario: Review a rollback request

- **WHEN** the learner selects the rollback control on a content-batch result
- **THEN** the Approval Gate replaces the composer and identifies the batch and the effect of rollback

#### Scenario: Approve rollback

- **WHEN** the learner approves the displayed rollback
- **THEN** the existing rollback operation is issued once for the displayed batch

#### Scenario: Cancel rollback

- **WHEN** the learner cancels the displayed rollback
- **THEN** the composer returns and no rollback request is issued

#### Scenario: Switch conversations while approval is open

- **WHEN** the learner changes conversations before deciding on a rollback
- **THEN** the gate closes and its old callback cannot roll back the prior batch

### Requirement: Agent Artifact handoff previews the saved Paper

A completed Agent turn that hands off a managed Paper SHALL show one Artifact card
in the conversation carrying the saved Paper's title and item count. The newest
Artifact of the current turn MAY open a temporary Adaptive Split preview beside
the central Lesson Kit page; the page SHALL remain present and readable, and the
preview SHALL NOT navigate away from it. Older Artifact cards restored from
history SHALL be shown collapsed and SHALL NOT open the split on their own.
An open live preview SHALL be retained in tab-scoped state with its conversation,
Paper, and route identity, and a same-tab reload SHALL restore it only when the
conversation and route still match. Explicit collapse, a new user turn, a
conversation switch, or native navigation SHALL clear that live-preview state.
Opening the Paper's canonical page remains an explicit learner action that goes
to the workspace's saved-paper page.

#### Scenario: A finished turn previews its Artifact

- **WHEN** a turn finishes with a managed Paper Artifact
- **THEN** one card appears in the conversation and its preview opens beside the central page

#### Scenario: The preview does not take over navigation

- **WHEN** the Artifact preview is open
- **THEN** the central Lesson Kit page remains present and no navigation occurs

#### Scenario: History restores cards without previewing

- **WHEN** the learner opens a conversation whose earlier turn already had an Artifact
- **THEN** that Artifact card is restored in the conversation without opening the split

#### Scenario: Keep a live preview across reload

- **WHEN** the latest Artifact preview remains open after its turn completes
  and the learner reloads the same tab on the same route
- **THEN** that live preview is restored only for the same conversation and route, without changing the current Lesson Kit page

#### Scenario: The learner opens the Paper page

- **WHEN** the learner activates the card's open action
- **THEN** the workspace's saved-paper page opens as an explicit navigation

### Requirement: Same-workspace middle navigation preserves the Agent rail

Navigating between pages and query states within one workspace SHALL update
only the middle page content and its route-owned lifecycle. The existing
`#ai-column` DOM and Agent controller SHALL remain mounted. Browser back and
forward SHALL follow the same behavior. Navigation SHALL update current page
context for future submissions while preserving the context already captured
by accepted work. External, cross-workspace, modified-click, download, and
explicitly targeted links SHALL keep native browser navigation.
The server-rendered `#ai-column` SHALL have the same structure on graph and
non-graph pages. Graph-only dashboard content SHALL belong to the graph middle
page, and selecting a graph node SHALL NOT hide or replace the Agent chat.

#### Scenario: Navigate within the workspace

- **WHEN** the learner follows a same-workspace page link from navigation, a
  page card, or middle content
- **THEN** the middle page changes while the existing Agent rail and its
  controller remain in place

#### Scenario: Navigate back or forward

- **WHEN** the learner uses browser Back or Forward after a same-workspace
  navigation
- **THEN** the middle page and its route-owned behavior change without
  rebuilding the Agent rail

#### Scenario: Send after navigating

- **WHEN** the learner sends a new message after changing the middle page
- **THEN** the request uses the current page context while previously accepted
  work retains its submitted context

#### Scenario: Enter and leave the graph page

- **WHEN** the learner enters or leaves the graph page within the same workspace
- **THEN** the graph dashboard mounts or disposes with the middle page while the
  same Agent rail remains visible and usable

#### Scenario: Follow a native navigation

- **WHEN** the learner uses a modified click, download, external link, or link
  to another workspace
- **THEN** the browser performs its normal navigation without middle-page
  interception

### Requirement: Unaccepted and uncertain Agent messages remain recoverable

Before clearing the composer, the UI SHALL save outgoing text, captured request
context, and a stable submission identity in browser storage. A definite
request rejection SHALL remain visible and editable/retryable across reload.
If acceptance is uncertain, the UI SHALL distinguish that state and reconcile
by retrying the same identity and task fields. Confirmed acceptance SHALL
remove the saved local copy and display the canonical accepted message or
pending state without duplicating it in the local recovery surface. Accepted queued messages SHALL appear only in the queue list; waiting-for-stop interrupt messages SHALL have one independent send status. A retry of an accepted failed turn SHALL be an explicit linked
attempt using the current accepted message text and its originally captured
context; it SHALL NOT reuse an old queue/interrupt choice as routing metadata.
Recovery SHALL NOT overwrite a newer composer draft or automatically replay a
provider operation or its writes.

#### Scenario: The request is rejected

- **WHEN** the turn endpoint rejects a submission before acceptance
- **THEN** the original text remains recoverable after reload and retry does not replace a newer draft

#### Scenario: The acceptance response is lost

- **WHEN** the client cannot establish whether a request was accepted
- **THEN** the visible state says acceptance is uncertain and a retry uses the same identity and task fields

#### Scenario: An accepted message is queued

- **WHEN** the server confirms a message is queued or waiting for stop confirmation
- **THEN** the local outbox copy is reconciled to that accepted turn; only queued messages enter the queue list, while an interrupt waiting for stop confirmation uses its independent send status

#### Scenario: An accepted turn fails

- **WHEN** the provider fails and the conversation is reopened
- **THEN** the original accepted message and failure status remain visible; any partial output is shown only when it exists

#### Scenario: Retry an accepted failure

- **WHEN** the learner explicitly retries a failed accepted turn
- **THEN** a new turn links to the original message, uses its current accepted text and original context, and both turns remain in history

#### Scenario: Multiple local recovery records

- **WHEN** rejected, uncertain or failed-message recovery records exist
- **THEN** one compact recovery summary with a count leads to individual explicit actions, and failed accepted turns retain their inline history actions; the UI does not stack repeated full-size recovery cards above the composer or classify recovery records as queued work

#### Scenario: Interrupt submission is rejected

- **WHEN** a distinct interrupt cannot be accepted because another interrupt handoff or a Paper approval is pending
- **THEN** the text remains recoverable without overwriting a newer draft, no queue entry is created, and the UI explains the blocking state

### Requirement: Provider activity cards show evidenced outcomes
The UI SHALL render normalized provider activities as semantic action cards with their actual status and outcome. Known impact SHALL come from normalized provider or backend evidence; unknown impact SHALL be identified as unknown. Diagnostics SHALL be folded and redacted, with a concise summary limited to 240 characters. The UI SHALL expose only backend-supported recovery controls and SHALL NOT present selective retry when no such operation exists. Existing approval behavior remains governed by its current capability contracts.

#### Scenario: A tool reports a result and an error
- **WHEN** normalized activity evidence contains a semantic action, terminal status, output, and diagnostic text
- **THEN** the card shows the action, actual status and evidenced result, while the redacted diagnostic stays folded

#### Scenario: Impact is not known
- **WHEN** an activity has no evidence of completed or failed effects
- **THEN** the card labels impact as unknown and does not infer success from a command string

#### Scenario: Selective recovery is unavailable
- **WHEN** a failed activity has no supported scoped retry operation
- **THEN** the UI offers no selective retry and may offer only an existing safe read-only or new-instruction affordance

### Requirement: Running-send preference and pending controls are explicit

The workspace's existing browser settings SHALL store the default action for a
message submitted while a turn is running, with queue as the default. The
composer SHALL retain explicit queue and interrupt-and-send choices regardless
of the configured default. A single compact pending-message list immediately above the composer SHALL show only accepted queued messages in confirmed execution order, with reorder, send-now, edit and remove controls before execution, and one continue action when retained work is paused. Interrupt handoffs SHALL NOT appear as queue entries. Pending edits
SHALL use the expected revision read with the message. The controls SHALL make
clear that an accepted pending message has not begun provider execution.

#### Scenario: Change the default running-send action

- **WHEN** the learner changes the running-send preference in workspace settings
- **THEN** the choice survives normal browser reopening and changes only future submissions

#### Scenario: Use an explicit running-send action

- **WHEN** a turn is running and the learner chooses queue or interrupt-and-send for one submission
- **THEN** that explicit action applies to the submission without changing the stored default preference

#### Scenario: Inspect and edit a pending message

- **WHEN** the learner opens an accepted message that has not started
- **THEN** its current text and order are shown, and a valid edit preserves the originally captured context

#### Scenario: Stale pending control

- **WHEN** the pending message has started or its revision changed before the learner edits or removes it
- **THEN** the UI reports that the pending state changed and refreshes the list without modifying the running message

#### Scenario: Continue paused work

- **WHEN** the conversation has retained paused messages and no provider turn is running
- **THEN** the learner can explicitly continue the queue and see the next retained message begin

#### Scenario: Interrupt result keeps older work paused

- **WHEN** D interrupts A while B and C are queued and D finishes
- **THEN** B and C remain visible as paused until the learner explicitly continues them

#### Scenario: Compact queued messages

- **WHEN** B and C are accepted with queue while A runs
- **THEN** the composer remains usable beneath one list with one compact row per message in execution order; no duplicate pending cards appear in history

#### Scenario: An empty queue is hidden

- **WHEN** no queued messages remain, including when an interrupt is waiting for stop confirmation
- **THEN** the entire queue list and its queue controls are hidden; any interrupt status is shown independently

#### Scenario: Reorder with accessible controls

- **WHEN** the learner moves C above B by dragging or the keyboard equivalent and the server accepts the expected order
- **THEN** the list and dispatch order both become C then B without changing their identities, text or captured contexts

#### Scenario: Queue reorder conflicts

- **WHEN** the queue changes before the server accepts a reorder
- **THEN** the UI refreshes the authoritative order and explains the conflict without silently persisting the stale order

#### Scenario: Send a queued message now

- **WHEN** the learner chooses send-now on queued C while A runs and B precedes C
- **THEN** C leaves the ordinary queue and uses direct interrupt-and-send with its existing identity, current text and original context; B stays paused

#### Scenario: Read long or numerous pending messages

- **WHEN** queued text is long or more than four messages are queued
- **THEN** rows offer full-text reading/editing, the list scrolls within at most four row heights, the composer stays visible, and icon actions have readable accessible names

### Requirement: Existing approval controls remain truthful and scoped
Governed Paper-reset and rollback confirmations SHALL show their exact impact and remain bound to the intended workspace/conversation/message/revision; cancellation or stale approval SHALL perform no write. Paper approval SHALL identify the existing Paper, proposed item membership/order change, and affected unfinished completion/draft counts from the existing backend preview. The Agent SHALL propose rather than apply this Paper update; a learner click SHALL cause the page to request the existing validated update. A preview snapshot or chat reply alone SHALL NOT constitute that click. This change adds no generic approval gate to ordinary tools.

Paper approval SHALL coexist with the ordinary composer. New messages explicitly submitted with queue SHALL be retained in the paused queue with their submission-time contexts. Interrupt-and-send and send-now SHALL be rejected without queue fallback or message loss; neither operation SHALL bypass the pending approval. Pending approval SHALL prevent queue continuation. Approval or cancellation SHALL leave the queue paused until the learner explicitly continues it. Existing rollback SHALL retain its composer-replacement interaction.

If the Paper or progress snapshot changed before approval, the UI SHALL perform no update, display a refreshed impact for the same proposed update and require a new approval click without requiring another Agent turn. Reload/reopen SHALL restore the pending approval and paused queue without automatic writes or provider execution. Missing/invalid targets SHALL produce actionable feedback without creating a replacement Paper. Duplicate approval attempts SHALL NOT reset progress twice.

#### Scenario: Cancel an existing Paper reset approval
- **WHEN** the learner cancels a governed Paper-reset approval or switches conversations before deciding
- **THEN** no Paper write occurs and the existing approval callback cannot act on the new conversation

#### Scenario: Approve the displayed Paper update
- **WHEN** the learner approves the current displayed Paper impact
- **THEN** the page requests the exact proposed update with its current confirmation; Paper ID, questions, historical attempts/ratings and other Papers remain unchanged, while only the target Paper's affected unfinished progress/drafts reset

#### Scenario: Continue composing while approval is pending
- **WHEN** B/C are already queued and the learner explicitly queues another message while a Paper update awaits approval
- **THEN** the composer stays usable and the new message joins the paused queue; no queued provider runs and Continue cannot bypass the approval

#### Scenario: Resolve approval before continuing the queue
- **WHEN** the learner approves or cancels the pending Paper update
- **THEN** the queue remains paused and requires explicit continuation, regardless of whether the update was approved or cancelled

#### Scenario: Practice advances before approval
- **WHEN** the learner answers more questions or the Paper changes before the approval request is validated
- **THEN** no update/reset occurs from the old confirmation, the latest impact is displayed for another click, and no additional Agent request is required

#### Scenario: Restore a pending Paper approval
- **WHEN** the learner reloads or reopens the owning conversation after a Paper approval was persisted
- **THEN** the pending decision and paused queue reappear, with no automatic update or provider launch and with impact revalidation before execution

#### Scenario: Navigate or switch conversations during approval
- **WHEN** middle navigation or a conversation switch occurs while approval is pending
- **THEN** middle navigation preserves the decision; switching conversations makes old callbacks inert, and any restored approval remains bound to its original workspace/conversation/turn/Paper/revision

#### Scenario: Repeat an approval request
- **WHEN** an approval is double-clicked or its response is lost and the decision is submitted again
- **THEN** the operation is not executed a second time and the UI does not claim a second reset

#### Scenario: Interrupt cannot bypass approval or silently queue

- **WHEN** the learner chooses interrupt-and-send or send-now while a Paper update awaits approval
- **THEN** the UI explains that approval must be resolved first, retains the composer text or original queued item, and neither starts a provider nor silently enqueues an interrupt message

### Requirement: Minimal Paper start and practice controls

The start surface SHALL show selected Paper title, item count, Answer Reveal Timing and start action. An unfinished run SHALL instead offer continuation with original timing, without restarting or changing timing. The old content-mode, rating-timing, quantity, save-from-selection and source-filter configuration block SHALL be absent. Ordinary navigation SHALL retain `上一题`, `下一题`, `不会`, plus `提交答案` only for multiple-choice and text in per-item mode. Paper-level `提交试卷` and `暂停练习` SHALL remain available; the obsolete session-only unsaved-content hint SHALL be removed. Locked-item mutation controls SHALL be disabled or absent without blocking navigation or self-rating edits.

#### Scenario: Start and resume
- **WHEN** a learner starts and later resumes a Paper
- **THEN** start selects timing and continuation restores it without the old setup block

#### Scenario: Navigate without submitting
- **WHEN** a learner navigates, pauses, or reaches the final item
- **THEN** the Paper is not submitted and pause is labelled `暂停练习`

### Requirement: Accessible Paper status dots

A compact numbered status-dot panel SHALL navigate to every item. Whole-Paper mode before submission SHALL distinguish unanswered, filled and stuck without showing correctness. Per-item mode SHALL show correct/wrong only with usable verdicts, and distinguish filled-but-unsubmitted from submitted-without-verdict. Current item SHALL have an outline or equivalent non-color cue. Statuses SHALL have readable accessible names, not color alone; many items SHALL not obscure the question or navigation.

#### Scenario: No premature grading cues
- **WHEN** answers are filled in whole-Paper mode before submission
- **THEN** colors, text, badges and summaries show filled status without exposing right/wrong

#### Scenario: Jump and read status
- **WHEN** any numbered dot is activated
- **THEN** the question appears with accessible status and a distinct current-item indicator

### Requirement: Independent self-rating during Paper practice

The run SHALL preserve its existing self-rating preference. When enabled, eligible items SHALL expose compact numeric 1–5 input and optional note after per-item submission or whole-Paper submission according to Answer Reveal Timing. Self-rating SHALL be optional, SHALL NOT gate navigation or completion, and SHALL remain editable through the existing same-run overwrite rule. Missing self-rating SHALL NOT mean correctness. Invalid or failed saves SHALL retain edits and report errors. When disabled, self-rating controls SHALL be absent and existing verdict-driven learning semantics SHALL remain unchanged. No record-and-next action SHALL be required.

#### Scenario: Rate a text answer
- **WHEN** a text answer is submitted in per-item mode with self-rating enabled
- **THEN** the learner may compare the reference and save a rating or continue without one

#### Scenario: Whole-Paper answers and optional ratings
- **WHEN** final submission contains eligible unrated items
- **THEN** completion succeeds and items remain available for later self-rating

#### Scenario: Edit or reject a rating
- **WHEN** a linked rating is edited
- **THEN** valid edits overwrite only that same-run rating/note without replaying learning effects
- **AND** empty or out-of-range saves are rejected without writes and the editor stays usable

#### Scenario: Self-rating disabled
- **WHEN** self-rating is disabled
- **THEN** answers/results work without rating inputs, note fields or feedback save actions

### Requirement: Paper completion and answer-sheet return

Successful explicit final submission SHALL show a congratulations-style surface with total items, objective correct/wrong, stuck and pending self-rating counts. Counts SHALL be truthful; overlapping stuck/wrong SHALL not be presented as disjoint totals, unavailable verdict SHALL not become wrong, and completion SHALL not claim all answers are correct. Actions SHALL include `查看本次答卷`, `再练一次`, `返回试卷列表`. Answer-sheet review SHALL permit arbitrary navigation with fixed recorded answers and editable eligible self-ratings, with an explicit return to the same run's completion surface without resubmission. Starting again SHALL create a distinct run and preserve the completed one.

#### Scenario: Review and return
- **WHEN** the learner views an answer sheet, changes item or self-rating, and returns to completion
- **THEN** the same run's completion and current rating counts appear without another Attempt or archive

#### Scenario: Practice again
- **WHEN** the learner starts again from completion
- **THEN** a new run starts from that Paper with a fresh start choice and the previous answer sheet remains intact

### Requirement: Question source display preference

The settings view and left rail SHALL expose the same per-workspace self-rating and question-source preferences, synchronize both entry points and browser tabs, and preserve explicit stored values. Question sources SHALL be hidden by default. Turning source display off or on SHALL immediately hide or show an available source on the current question without navigation, restarting or losing inputs. Hiding a source SHALL NOT remove its persisted provenance.

#### Scenario: Source starts hidden and can be toggled on the current question
- **WHEN** a workspace has no explicit source preference and a question has source evidence
- **THEN** the source is hidden by default
- **AND** enabling, disabling and reenabling the preference updates that same question immediately

#### Scenario: Explicit preferences and both entry points agree
- **WHEN** the learner changes either preference in the left rail, settings view or another tab for that workspace
- **THEN** both entry points and the visible question reflect that value without changing another workspace's preferences

### Requirement: Paper pixel progress and confirmed-answer feedback

Paper practice SHALL display a pixel progress band whose completion reflects answered or stuck items in per-item mode and filled or stuck items in on-submit mode, never the cursor or correctness percentage. Its palette SHALL progress from deep orange through yellow to sky blue, using square cells and eight brightness levels. Equal-width compression and rarefaction bands SHALL travel horizontally, with denser regions brighter and the integrated grey-white end cell brightening as a compression arrives. Wave speed and contrast SHALL grow with completion.

A newly confirmed correct per-item answer SHALL bounce the visible question and option cards twice. Every five consecutive objective correct answers SHALL show the approved rectangular blue/yellow banner with smooth italic combo revealed by a paintbrush and a temporary alternate-color density band. Failed requests, navigation, archived review, self-rating, ungraded answers and on-submit drafts SHALL NOT trigger correct-answer or combo feedback.

#### Scenario: Cursor does not masquerade as completion
- **WHEN** a learner navigates to the last item without answering
- **THEN** pixel completion remains based on the answered or filled item states

#### Scenario: Confirmed per-item streak
- **WHEN** five consecutive objective correct answers have been confirmed in per-item mode
- **THEN** the combo banner appears once and does not change progress or create additional writes

### Requirement: Paper completion celebration settles into real results

After successful final submission and successful archived-run readback, the completion card SHALL enter prominently with colorful confetti behind it, then settle into the central completion view with actual counts and per-item status/review links below it. The same card SHALL remain in the result view. Existing review, retry, again and return actions SHALL remain usable. Loading an archived record or returning from review SHALL show the stable result without replay. A failed submission or failed readback SHALL NOT fabricate results or play successful celebration.

The Paper animation SHALL obey the existing motion preference: explicit on permits full motion, explicit off disables it, and the system reduced-motion preference disables continuous and ceremonial motion when no explicit on is set. Reduced motion SHALL immediately present the same stable card, accurate progress and results, with no confetti. Hidden documents SHALL stop scheduling animation frames; disposal on middle navigation SHALL cancel frames, timers, observers and transient decoration.

#### Scenario: Successful submit and settling
- **WHEN** final submission and archived readback succeed
- **THEN** the card celebrates once, settles, and the real item results become visible

#### Scenario: Reduced motion and historical review
- **WHEN** reduced motion is effective or an archived result is opened
- **THEN** the final card and real results are immediately available without ceremonial motion
