## Purpose

The workbench UI is the minimal consumption surface of lesson-kit: a three-column
shell with a left navigation column (practice, knowledge points, knowledge
graph), a middle page area, a session-end self-rating step, and a right AI
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

The practice page SHALL be the departure surface for deciding what to practise
and for resuming/running the current Paper. With no active Practice Run it MAY
show scope, source/difficulty filters, suggestions, saved/recent Papers, rating
preference, and other assembly inputs; these inputs constrain Paper Assembly and
are not themselves an executable queue. Starting from a knowledge scope SHALL
first determine a Paper's ordered items, then start the Practice Run from that
fixed Paper.

The learner-facing page SHALL NOT expose per-problem manual selection. Existing
content-mode controls MAY remain temporarily as compatibility inputs while the
mixed-format Paper UI is migrated, but they SHALL NOT define the product identity
of a Paper or authorize dynamic pulling after execution begins. During an active
run, the middle column MAY collapse arrangement controls so the fixed Paper's
answering flow is primary; ending the run returns to the departure surface.

#### Scenario: Start from an explicit scope

- **WHEN** the learner chooses a knowledge scope and starts practice
- **THEN** Lesson Kit assembles a Paper from that scope before execution and the resulting Practice Run keeps that ordered item list fixed

#### Scenario: Resume an active Paper

- **WHEN** the learner returns to practice with an unfinished active run
- **THEN** the same Paper and progress are offered for resume without re-running assembly

#### Scenario: Filters do not mutate a running Paper

- **WHEN** source, difficulty, or suggestion inputs change while a Paper is already running
- **THEN** the current run is unchanged and those inputs apply only to a later Paper Assembly

#### Scenario: No manual problem picker

- **WHEN** the learner opens the practice departure controls
- **THEN** scope and filter controls may be present but no control can hand-pick a concrete problem into the Practice Run

### Requirement: Compact per-problem self-rating

In per-problem mode with the learner's show-rating preference on, the revealed
feedback area SHALL use a compact two-surface form: one direct numeric 1–5
input and one optional note surface with the explicit `记录并下一题` action. It
SHALL retain accessible field names and SHALL NOT expand the rating into five
separate choice controls. Rating validation and feedback-write timing SHALL
remain unchanged. With the preference off, the feedback area SHALL NOT appear;
an objective problem's verdict and the revealed solution SHALL be followed by a
single explicit `下一题` action that advances without a feedback write, and an
empty or out-of-range rating SHALL be rejected inline at the input.

#### Scenario: Enter a compact per-problem rating

- **WHEN** the learner reaches self-rating in per-problem mode with rating shown
- **THEN** the feedback area shows a direct numeric 1–5 input and an optional
  note in two compact rounded surfaces
- **AND** one explicit `记录并下一题` action records the feedback and advances
- **AND** no five-choice rating group is rendered

#### Scenario: Reject an invalid compact rating in place

- **WHEN** the learner enters a value outside 1-5 — or leaves the input empty —
  in the compact form
- **THEN** the visible card reports the validation error and no feedback
  request is sent

#### Scenario: Off mode advances without a feedback write

- **WHEN** the preference is off and the learner submits a problem, then presses
  `下一题`
- **THEN** the next unseen problem is shown and no feedback request is sent

#### Scenario: Off mode hides the rating surface entirely

- **WHEN** the preference is off and a problem's solution is revealed
- **THEN** no rating input, note surface, or `记录并下一题` action appears

### Requirement: Session-end unified self-rating

The session-end view SHALL present completed, unrated Paper items only when the
run uses unified self-rating. Each eligible item SHALL show the learner answer
and solution with a 1–5 input and optional note. Submitting a score SHALL use the
ordinary feedback behavior once and remove the scored item; skipped and
unfinished items SHALL not be fabricated as completed ratings.

A practice-similar action MAY use the finished Paper's results and knowledge
scope as inputs to **assemble a new Paper**. It SHALL NOT reopen, extend, or
mutate the completed Practice Run.

#### Scenario: Rate completed items at run end

- **WHEN** the learner submits a score for one completed Paper item
- **THEN** feedback is recorded once and that item is removed while other unrated completed items remain

#### Scenario: Practice similar after the run

- **WHEN** the learner chooses the practice-similar action
- **THEN** Lesson Kit starts a new Paper Assembly from relevant scope/evidence and does not reuse the prior run as a mutable queue

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
When the current tab has no open conversation, the Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require one explicit provider selection; the provider SHALL be immutable after creation. Rename and delete SHALL be available from compact history-row menus only.

The chat state SHALL contain only an icon-only return-to-list control with an accessible label, the message stream, the input area, and a stop control while a turn is running. It SHALL NOT show provider settings, session settings, identity labels, current-page context text, daily-create controls, or chat-page rename/delete controls.

The client SHALL NOT read or write provider-memory or daily-create browser keys, auto-open the first session, auto-create a daily session, or initialize the removed explain/diagnose task console. Server-side context construction and existing compatibility APIs remain unchanged.

#### Scenario: Chat is quiet

- **WHEN** a learner opens an existing conversation
- **THEN** the chat view shows only the accessible icon back control, messages, input, and any running stop control

#### Scenario: History is the first view

- **WHEN** a workbench page loads with no conversation open in the current tab
- **THEN** the Agent column shows the session list and no session is opened or created

#### Scenario: Return to history

- **WHEN** the learner activates the back icon
- **THEN** the history list returns without creating a session or learning record

#### Scenario: History row actions

- **WHEN** the learner chooses rename or delete from a history-row menu
- **THEN** the corresponding local mirror action runs; those controls are absent from chat view

### Requirement: Agent rail keeps the open conversation across page navigation

The Agent rail SHALL keep the conversation the learner left open when the
central Lesson Kit view changes or the page reloads in the same tab. Returning
to the conversation list SHALL be an explicit learner action. When the
conversation that would be restored no longer exists, the rail SHALL fall back
to the conversation list without an error wall and SHALL NOT create a
conversation. Other read failures SHALL keep that conversation selected and
show a recoverable read error without discarding the selection.

#### Scenario: Switch the central view

- **WHEN** the learner has a conversation open and moves to another workbench page
- **THEN** the rail restores that conversation instead of the conversation list

#### Scenario: Reload the page

- **WHEN** the learner reloads the workbench page in the same tab
- **THEN** the rail restores the conversation that was open

#### Scenario: Return to the list explicitly

- **WHEN** the learner activates the return-to-list control
- **THEN** the conversation list returns and later page changes or reloads keep the list

#### Scenario: The open conversation disappears

- **WHEN** the conversation left open no longer exists in the workspace
- **THEN** the rail falls back to the conversation list without an error wall and creates no conversation

#### Scenario: Restoring the open conversation temporarily fails
- **WHEN** reading the conversation fails for a reason other than a confirmed missing conversation
- **THEN** the rail keeps that conversation selected, displays a recoverable read error, and preserves the selection for a later retry

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

### Requirement: Practice page suggestions and assembly entry

The practice page SHALL NOT maintain a Staged Practice List as a second product
object between knowledge scope and Paper. The learner's explicit knowledge-point
selection is Paper-assembly scope and may be summarized compactly; removing a
scope item SHALL update that selection everywhere it is represented.

The page MAY offer one on-demand suggestion entry sourced from the daily plan and
due scheduling state, deduplicated to one row per knowledge point with at most
one human-readable reason phrase. A suggestion action SHALL mean `据此组卷` (or
equivalent assembly intent): it can establish/prefill a Paper scope, but it
SHALL NOT join a knowledge point to an executable queue or inject concrete
problems into an active Practice Run. Raw scheduler parameters remain hidden.
The time view MAY remain beside the departure controls.

#### Scenario: A due knowledge point appears as an assembly suggestion

- **WHEN** a knowledge point is overdue and not already in the explicit assembly scope
- **THEN** the suggestion surface may show it with one reason phrase and an action to assemble from it, without a staged-list join action

#### Scenario: Remove a scope item

- **WHEN** the learner removes one knowledge point from the practice departure scope summary
- **THEN** that point is deselected in the knowledge list, graph, and scope tray without altering any running Paper

#### Scenario: Nothing selected and nothing suggested

- **WHEN** no assembly scope, saved/recent Paper, or suggestion is available
- **THEN** the practice departure page shows an honest compact empty state rather than inventing a staged practice queue

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

### Requirement: Cross-page practice-scope tray

Every workspace page SHALL expose one compact Paper-assembly scope control at the
upper-right of the middle column. Activating it SHALL open a tray that lists the
complete names of explicitly selected knowledge points, allows an item to be
removed, and offers one action to enter the practice departure page with that
scope. The tray SHALL reuse existing tab-local selection and SHALL NOT create
server-side learning or execution state.

The tray action SHALL NOT directly start a Practice Run. Scope answers what the
learner wants to practise; the practice page/Agent determines the concrete Paper
before execution. Open/collapsed state may remain browser-only.

#### Scenario: Inspect a long scope

- **WHEN** the learner opens the tray with more selected knowledge points than fit in its bounded list area
- **THEN** every selected name remains available through vertical scrolling without expanding the page header

#### Scenario: Remove a selected point from the tray

- **WHEN** the learner removes one knowledge point in the tray
- **THEN** it disappears from the tray and is deselected in other scope representations without changing a running Paper

#### Scenario: Enter practice from the tray

- **WHEN** at least one knowledge point is selected and the learner activates the tray action
- **THEN** the practice departure page opens with the same Paper-assembly scope and no Practice Run begins until a Paper is determined

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

The 组卷 page SHALL let a learner read the problems a saved paper holds without
leaving the page. Each item SHALL be an expandable block whose summary keeps the
index, title and reorder/remove controls it has today, and whose opened body
shows the problem's full text together with its recorded source line when one
exists. The body SHALL render through the same safe Markdown subset as the
knowledge point page's linked problems, so mathematics, figures and code render
identically on both surfaces. Items SHALL arrive collapsed, and the disclosure
affordance SHALL be visible on every item. Expanding an item SHALL change
nothing about the paper: the preview is a reading surface, never a second
editor.

#### Scenario: Read one problem of a saved paper

- **WHEN** a learner opens an item of a saved paper card
- **THEN** the problem's own text appears under the item title, with its source
  line when one is recorded

#### Scenario: A long paper stays scannable

- **WHEN** a saved paper holds dozens of problems
- **THEN** every item is collapsed on arrival and the card lists titles only

#### Scenario: Preview does not disturb the paper

- **WHEN** items are expanded and the learner then moves or removes items
- **THEN** those controls act on the same item rows as before, and only the
  saved order changes

### Requirement: Saved paper cards fold

The 组卷 page SHALL present every saved paper as a foldable card: the head — the
paper's title, its size, and its controls — stays visible while the problem list
folds away beneath it. Cards SHALL arrive folded, so the page reads as the
learner's papers rather than the concatenation of their problems. Within a
browser tab, a card the learner opened SHALL come back open after the reload an
edit performs: moving or removing items must not require re-opening the paper
after every click. Folding SHALL be a reading state only — opening or closing a
card sends no request and changes no stored order. A control in the head SHALL
act on the paper without folding the card as a side effect.

#### Scenario: A folded card shows its head only

- **WHEN** the 组卷 page renders saved papers
- **THEN** each card shows its title, its size and its controls, with its
  problem list folded away

#### Scenario: An edit leaves the paper open

- **WHEN** a learner opens a paper, moves one of its problems, and the page
  reloads the saved order
- **THEN** that paper is open again in that tab

#### Scenario: A control does not fold the card

- **WHEN** a learner presses 导出 or 开始练习 on an open card
- **THEN** the control runs and the card stays as the learner left it

#### Scenario: An error remains visible on a folded card

- **WHEN** a rename or export command fails while its paper card is folded
- **THEN** the error status remains visible outside the folded problem list

### Requirement: Learner settings in the left rail

The workbench's left column SHALL carry a settings section whose preferences
apply across the practice and paper surfaces. Its first preference SHALL be a
checkbox, 「练习与组卷显示自评」, defaulting to on: self-rating behaves exactly
as before. With it off, no self-rating surface SHALL appear anywhere in the
flow — the rating-timing choice is hidden and not required to start, the
feedback panel never renders, a finished round takes the no-session-end path,
and records label the round 关闭自评. The preference SHALL persist per
workspace in the browser across tabs and restarts, and SHALL take effect at the
next round's start; a running round keeps the mode it started with.

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
pending state. A retry of an accepted failed turn SHALL be an explicit linked
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
- **THEN** the local outbox copy is reconciled to that accepted turn and the pending list shows its current text and status

#### Scenario: An accepted turn fails

- **WHEN** the provider fails and the conversation is reopened
- **THEN** the original accepted message and failure status remain visible; any partial output is shown only when it exists

#### Scenario: Retry an accepted failure

- **WHEN** the learner explicitly retries a failed accepted turn
- **THEN** a new turn links to the original message, uses its current accepted text and original context, and both turns remain in history

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
of the configured default. A pending-message list SHALL show accepted text,
order, and paused or waiting status, with edit/remove controls only before
execution and a continue action when retained work is paused. Pending edits
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
