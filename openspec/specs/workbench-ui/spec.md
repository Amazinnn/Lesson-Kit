## Purpose

The workbench UI is the minimal consumption surface of lesson-kit: a three-column
shell with a left navigation column (practice, knowledge points, knowledge
graph), a middle page area, a session-end self-rating step, and a right AI
conversation column whose context display prioritizes the current problem
without ever limiting what the agent can see. Visual style copies the DeepSeek
Harness design system.
## Requirements
### Requirement: Three-column shell with navigation

The workbench SHALL render a three-column desktop layout: a left navigation column with workspace and study navigation, a primary middle page, and a collapsible right Agent conversation column, with workspace/course/chapter context in the top bar. At narrow widths the middle page SHALL remain the single primary column; the left and right columns SHALL become dismissible drawers opened by two compact icon controls in the top bar. Switching workspaces or pages SHALL preserve recorded pool state.

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

### Requirement: Practice page

The practice page SHALL require a learner-selected self-rating mode before beginning a multi-problem weak-point-first or explicitly knowledge-point-scoped session. It SHALL show one reading card at a time, send already seen problem ids with later pulls, and restore the selected mode, current card, seen ids, and unified-rating queue after same-tab refresh or navigation. Cards SHALL lead with `display_title`, not a raw id. In per-problem mode, answer submission reveals the solution and presents a 1-5 input, optional note, and one primary `保存并下一题` action. In unified mode, completed cards advance without rating and are assessed only after the question stage ends. Skipping and early ending SHALL remain zero-write until an explicit rating.

#### Scenario: Start with a selected mode

- **WHEN** the learner opens a new practice session
- **THEN** no problem is pulled until exactly one rating mode is selected and the learner starts

#### Scenario: Restore an active card

- **WHEN** the learner refreshes practice in the same tab with an active card
- **THEN** the same titled card and mode return without clearing the seen ids or pending unified ratings

#### Scenario: Practice with reveal-then-feedback

- **WHEN** a learner submits an answer in per-problem mode
- **THEN** the card reveals its non-empty solution before rating is accepted

#### Scenario: No repeats in a session

- **WHEN** the page pulls a later problem
- **THEN** every prior seen id is excluded and no card repeats

#### Scenario: Reject an invalid rating in place

- **WHEN** the learner enters a value outside 1-5
- **THEN** the visible card reports the validation error and no feedback request is sent

#### Scenario: End a unified-rating session early

- **WHEN** the learner ends a unified-rating session before exhaustion
- **THEN** completed cards enter unified self-rating without a persistent write before each rating submission

### Requirement: Session-end unified self-rating

The session-end view SHALL present completed, unrated cards only for a unified-rating session. Each card SHALL show the learner answer and solution with a 1–5 input and optional note. Submitting a card’s score SHALL use the ordinary feedback behavior once and remove the scored card; skipped and unfinished problems SHALL not appear.

#### Scenario: Rate completed cards at session end

- **WHEN** the learner submits a score for one completed card
- **THEN** feedback is recorded once and that card is removed while other cards remain

#### Scenario: Rate pending problems at session end

- **WHEN** the learner completes a unified-rating session with unrated cards
- **THEN** only completed, unrated cards are listed for scoring

#### Scenario: Practice similar from the session end

- **WHEN** the learner clicks the single practice-similar entry after a session ends
- **THEN** a new session begins for the same weak knowledge-point groups and does not reuse the prior seen-id set

### Requirement: AI column with priority context

The AI column SHALL display the current problem and recently viewed problems as
priority context, purely as a display hint. The column SHALL NOT restrict what
the external agent can see: the agent reaches all records through the CLI data
interface and can search freely. The learner SHALL be able to start an explain
or diagnose task for the current problem with one click (carrying answer text
and stuck-step markers), poll the task status, and view rendered results. New
conversations SHALL be startable at any time. With no provider configured, AI
actions SHALL show a graceful "configure the bridge" message and recording
continues unaffected.

#### Scenario: Explain the current problem

- **WHEN** the learner clicks "explain" for the current problem with an answer text present
- **THEN** a bridge task is created carrying the problem and the answer text, the column shows its status, and the validated result renders when done

#### Scenario: No provider configured

- **WHEN** the learner clicks "explain" and no bridge provider is configured
- **THEN** the column shows a graceful message that the bridge needs configuration, and practice recording is unaffected

#### Scenario: Agent sees beyond the priority context

- **WHEN** the agent works in the workspace
- **THEN** it can query all attempts, feedback, and signals through the CLI data interface, regardless of what the column displays as priority context

### Requirement: Knowledge point display page

The knowledge-point page SHALL render the body as its primary reading content and provide one prominent `练习此知识点` action. Activating it SHALL start a continuous non-repeating practice session scoped to that knowledge point. Linked formal problems SHALL remain reading-only, grouped by topic and collapsed by default; opened rows SHALL show `display_title` and the complete safe-rendered problem statement without summary text, truncation, ellipsis, raw ids, or per-problem practice controls. Raw signal and scheduler parameters SHALL not be shown.

#### Scenario: Practice one knowledge point

- **WHEN** a learner activates `练习此知识点`
- **THEN** practice opens with that knowledge point as the pull scope and continues through unseen linked problems

#### Scenario: Browse grouped linked problems

- **WHEN** a knowledge point has linked problems from multiple topics
- **THEN** the page displays separate collapsed labeled groups whose rows are reading-only

#### Scenario: Open a topic group

- **WHEN** a learner opens a linked-problem topic group
- **THEN** it reveals titled rows with the complete rendered statement and no nested summary or full-text disclosure

#### Scenario: Read a complete linked problem

- **WHEN** the learner opens a topic group
- **THEN** each row shows the title and complete rendered statement without summary, truncation, raw id, or an independent practice button

#### Scenario: Read a long linked problem

- **WHEN** a linked problem exceeds 500 normalized characters
- **THEN** its complete statement is shown and any compatible display summary is not rendered

#### Scenario: Read a short linked problem

- **WHEN** a linked problem is at most 500 normalized characters
- **THEN** its complete statement is shown without generated summary or truncation

#### Scenario: Missing long-problem summary

- **WHEN** a long linked problem has no display summary
- **THEN** its title and complete statement remain readable without fallback excerpt or ellipsis

#### Scenario: Long statement has no summary

- **WHEN** a long statement's compatible summary field is empty
- **THEN** the linked row does not create or display a summary layer

#### Scenario: Missing display title

- **WHEN** a linked problem lacks a display title
- **THEN** the row uses the fixed readable fallback `未命名题目` rather than a raw id or statement fragment

#### Scenario: Navigate a wiki link

- **WHEN** rendered knowledge content contains a valid workspace knowledge-point wiki link
- **THEN** activating it opens that formal knowledge-point route

#### Scenario: See signal reasons

- **WHEN** the Agent receives authoritative context for this knowledge point
- **THEN** complete signal reasons remain available there while the student page shows only a concise action reminder

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

The knowledge graph page SHALL render the live complete chapter graph in a middle-column canvas that fills the viewport below its compact page tools. Six deterministic component layouts SHALL supply seed positions before every visible node enters one unbounded unified elastic field. Existing edge attraction SHALL determine variable semantic gaps from 72 to 144 pixels in addition to endpoint radii, and every pair of node circles SHALL retain at least 24 pixels of logical clearance. The graph SHALL retain search, filter, zoom, pan, camera-only fit, drag, problem-count radius, focus, and the concise dashboard. Coordinates, soft anchors, motion, and interactions SHALL remain memory-only.

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
- **THEN** the middle area displays the live complete chapter graph

#### Scenario: Graph artifact missing

- **WHEN** no rendered graph artifact exists on disk
- **THEN** the graph remains available from current workspace data

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

For each turn, the browser SHALL send object identifiers rather than page DOM, and the server SHALL rebuild authoritative workspace, course, chapter, route, page type, selected object, and relevant learning context from SQLite. Practice, knowledge-point, and graph pages SHALL attach their defined object/state summaries. The latest three different browser-session object anchors SHALL also be attached. Unsubmitted answer and note drafts SHALL remain excluded, and the chat UI SHALL expose no draft-attachment setting.

#### Scenario: Ask about a knowledge point page

- **WHEN** the learner sends a turn from a knowledge-point page
- **THEN** the Agent receives current content, evidence, schedule, neighbours, and related problems rebuilt from the workspace

#### Scenario: Keep a practice draft private

- **WHEN** an unsubmitted answer or note exists
- **THEN** it is absent from Agent context and is not persisted by the conversation bridge

#### Scenario: Attach a practice draft explicitly

- **WHEN** a learner sends an Agent turn while an unsubmitted practice draft exists
- **THEN** the draft remains excluded because the student chat exposes no attachment setting

### Requirement: User-visible Markdown uses one safe subset
All user-visible learning text SHALL use the same supported Markdown subset: ATX headings through level 3, paragraphs, ordered and unordered lists, blockquotes, fenced and inline code, strong/emphasis, safe http(s) links, wiki links, math, and workspace-local images.

#### Scenario: Agent answer renders Markdown
- **WHEN** an Agent or student message contains `##`, `**bold**`, a list, or a fenced code block
- **THEN** the message displays semantic headings, emphasis, list markers, and code styling rather than raw Markdown syntax

#### Scenario: Unsafe markup is rejected
- **WHEN** text contains raw HTML, a `javascript:` link, or an image path outside the workspace figure directory
- **THEN** the rendered output contains escaped text and no executable link or image

### Requirement: Streaming text is one message
Partial Agent text events SHALL update one assistant message until the turn completes.

#### Scenario: Partial events coalesce
- **WHEN** a turn emits several text events
- **THEN** the UI shows one growing assistant message and renders the combined Markdown

### Requirement: The default Agent view is a session list
The Agent column SHALL initially show the complete local conversation list without opening or creating a session. New conversation creation SHALL require one explicit provider selection; the provider SHALL be immutable after creation. Rename and delete SHALL be available from compact history-row menus only.

The chat state SHALL contain only an icon-only return-to-list control with an accessible label, the message stream, the input area, and a stop control while a turn is running. It SHALL NOT show provider settings, session settings, identity labels, current-page context text, daily-create controls, or chat-page rename/delete controls.

The client SHALL NOT read or write provider-memory or daily-create browser keys, auto-open the first session, auto-create a daily session, or initialize the removed explain/diagnose task console. Server-side context construction and existing compatibility APIs remain unchanged.

#### Scenario: Chat is quiet

- **WHEN** a learner opens an existing conversation
- **THEN** the chat view shows only the accessible icon back control, messages, input, and any running stop control

#### Scenario: History is the first view

- **WHEN** a workbench page loads
- **THEN** the Agent column shows the session list and no session is opened or created

#### Scenario: Return to history

- **WHEN** the learner activates the back icon
- **THEN** the history list returns without creating a session or learning record

#### Scenario: History row actions

- **WHEN** the learner chooses rename or delete from a history-row menu
- **THEN** the corresponding local mirror action runs; those controls are absent from chat view

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
Deleting an idle session SHALL remove only its Lesson Kit mirror directory. A running session SHALL return a conflict and remain intact.

#### Scenario: Returning to history
- **WHEN** a student clicks back from a conversation
- **THEN** the list view returns without creating or modifying a learning record

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

The graph SHALL remain fully static after the force simulation settles. It SHALL reheat only after a learner interaction or viewport/model change such as dragging, filtering, focusing, resizing, or changing global gravity. It SHALL NOT apply a continuous idle breathing offset. Labels SHALL remain readable under the existing focus and zoom rules, and raw identifiers SHALL NOT be primary canvas text.

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

### Requirement: Adjustable graph compactness

The existing 0–100 in-memory center-gravity control SHALL provide a visibly stronger range, with a maximum coefficient of approximately `0.00351` and default value 30. Higher values SHALL draw all nodes more toward the graph center and lower values SHALL let them spread, regardless of whether nodes have connecting edges. The value SHALL NOT be persisted or written to learning records.

#### Scenario: Increase graph gravity

- **WHEN** the learner raises the gravity control
- **THEN** the current simulation reheats with a stronger center force and the graph remains otherwise unchanged

#### Scenario: Lower graph gravity

- **WHEN** the learner lowers the gravity control
- **THEN** the current simulation reheats with a weaker center force and unconnected nodes may spread farther apart

