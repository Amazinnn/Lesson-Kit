## MODIFIED Requirements

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

### Requirement: Knowledge graph page

The knowledge graph page SHALL render the current complete chapter graph from live workspace data. It SHALL retain search, filter, zoom, pan, drag, fit, readable external labels, problem-count node radius, and semantic-strength edges. Connected components SHALL be laid out independently from six deterministic starts and packed; isolates SHALL occupy a separate readable region and residual close edges MAY render as shallow curves. Selecting a node SHALL emphasize one-hop and two-hop context while fading farther topology, and selecting the background SHALL restore the full graph. Coordinates and interactions SHALL remain memory-only.

#### Scenario: Lay out disconnected graph data

- **WHEN** the current graph contains several components and isolates
- **THEN** independently selected layouts are packed without collapsing all nodes around one center

#### Scenario: See a current graph state

- **WHEN** underlying knowledge-point state changes through a compatible explicit operation and the graph refreshes
- **THEN** live workspace data controls its visual presentation without exposing a manual state editor

#### Scenario: Read coverage and closeness

- **WHEN** nodes have different formal-problem counts and edges have different attraction
- **THEN** node radius expresses formal-problem count and stronger semantic edges retain shorter target distances within their component

#### Scenario: Navigate the graph directly

- **WHEN** the learner drags a node, pans, zooms, or fits the graph
- **THEN** the complete graph updates in memory and remains navigable

#### Scenario: Filter the visible graph

- **WHEN** the learner searches or applies an available filter
- **THEN** visible components are recomputed and packed without persisting removed coordinates

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
- **THEN** the node and one-hop neighbors remain fully emphasized, two-hop neighbors remain secondary, and farther nodes plus unrelated edges fade

#### Scenario: Reset focus

- **WHEN** the learner selects the graph background
- **THEN** the complete graph returns to normal emphasis

#### Scenario: Reheat after interaction

- **WHEN** the learner filters, resizes, or drags a node
- **THEN** applicable component layouts reheat without persisting coordinates

#### Scenario: Prefer reduced motion

- **WHEN** the browser reports reduced motion
- **THEN** the graph computes the best stable component layouts and paints once

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

## ADDED Requirements

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
