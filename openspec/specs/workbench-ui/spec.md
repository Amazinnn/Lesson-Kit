## Purpose

The workbench UI is the minimal consumption surface of lesson-kit: a three-column
shell with a left navigation column (practice, knowledge points, knowledge
graph), a middle page area, a session-end self-rating step, and a right AI
conversation column whose context display prioritizes the current problem
without ever limiting what the agent can see. Visual style copies the DeepSeek
Harness design system.
## Requirements
### Requirement: Three-column shell with navigation

The workbench SHALL render a three-column layout: a left navigation column with
a workspace dropdown, navigation entries for practice, knowledge points, and
the knowledge graph, plus the weak knowledge point list; a middle page area; a
right AI conversation column (collapsible); and a top bar showing the
workspace, course, and chapter. The visual style SHALL follow the DeepSeek
Harness design tokens (background, text, brand color, pill buttons, radii,
shadows). Switching workspaces or pages SHALL not lose learning state, because
all state lives in the pool.

#### Scenario: Navigate from the left column

- **WHEN** the learner clicks a navigation entry in the left column (practice, knowledge points, knowledge graph)
- **THEN** the middle area shows the corresponding page for the current workspace

#### Scenario: Switch workspace without losing state

- **WHEN** the learner switches the workspace dropdown in the left column
- **THEN** the middle area reloads for the new workspace and previously recorded attempts, feedback, and signals remain intact in the pool

### Requirement: Practice page

The practice page SHALL require a learner-selected self-rating mode before beginning a multi-problem weak-point-first session. It SHALL show one reading card at a time and SHALL send already seen problem ids with every later pull so no problem repeats in a session. In per-problem mode, answer submission reveals the solution and presents a 1–5 input, optional note, and one primary “保存并下一题” action. In unified mode, completed cards advance without rating and are assessed together only after the question stage ends. The page SHALL offer visible “跳到下一道题目” and “提前结束本次练习” actions, and SHALL NOT present step-stuck or ungraded-next feedback buttons.

#### Scenario: Start with a selected mode

- **WHEN** the learner opens the practice page
- **THEN** no problem is pulled until exactly one rating mode is selected and the learner starts the session

#### Scenario: Practice with reveal-then-feedback

- **WHEN** a learner submits an answer in per-problem mode
- **THEN** the card reveals its solution before the learner can enter the rating and optional note

#### Scenario: No repeats in a session

- **WHEN** the practice page pulls later problems in one session
- **THEN** every pull excludes prior problem ids and the same problem is not rendered twice

#### Scenario: End a unified-rating session early

- **WHEN** the learner ends a unified-rating session before the pool is exhausted
- **THEN** no new problem is pulled and completed cards enter the unified self-rating view without persistent writes before rating submission

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

The knowledge point display page SHALL render linked problems grouped by their topic label. Each row SHALL present a concise problem title as primary text. Problems whose normalized statement exceeds 300 characters MAY present a persisted Chinese one-sentence summary of at most 48 characters as secondary text. Every row SHALL allow the learner to reveal the complete problem statement without runtime truncation. Raw problem ids and ellipsis-truncated statement excerpts SHALL NOT appear in linked-problem rows.

#### Scenario: Browse grouped linked problems

- **WHEN** a knowledge point has linked problems from multiple topics
- **THEN** the page displays separate labeled groups containing concise problem titles

#### Scenario: Read a long linked problem

- **WHEN** a linked problem exceeds 300 normalized characters and has a valid display summary
- **THEN** its row shows the complete stored summary and can reveal the full statement without an ellipsis

#### Scenario: Read a short linked problem

- **WHEN** a linked problem is at most 300 normalized characters
- **THEN** its row shows the title without manufacturing a secondary excerpt and can reveal the full statement

#### Scenario: Missing long-problem summary

- **WHEN** a long linked problem has no valid persisted summary
- **THEN** its row shows the title and full-statement disclosure without falling back to a truncated excerpt

#### Scenario: Navigate a wiki link

- **WHEN** the learner clicks a wiki link in a knowledge point body
- **THEN** the display page navigates to the linked knowledge point

#### Scenario: See signal reasons

- **WHEN** the knowledge point has signals or cascade boosts
- **THEN** the display page shows the signal weight and the cascade reason text

### Requirement: Knowledge point list page

The knowledge point list and the left weak-point rail SHALL use each knowledge point’s readable name as primary text and show raw identifiers only as secondary context.

#### Scenario: Read weak points without decoding identifiers

- **WHEN** the learner views the weak-point rail
- **THEN** every entry is identifiable from its knowledge-point name without relying on its raw id

#### Scenario: Open the knowledge point list

- **WHEN** the learner clicks the knowledge point navigation entry
- **THEN** the middle area lists the chapter's knowledge points in weak order, each linking to its display page

### Requirement: Knowledge graph page

The knowledge graph page SHALL render the current chapter graph from live workspace data inside the workbench rather than embedding a generated artifact. The middle column SHALL provide graph search, state filtering, zoom, pan, drag, fit, and focus. Nodes SHALL be circular with external readable labels; current state SHALL control color and the formal-problem count SHALL control radius. Connected nodes SHALL be positioned by a force simulation in which stronger semantic edges have shorter target distances. The outer right column SHALL switch between knowledge-point detail and the existing AI teacher panel; the graph SHALL NOT render its own nested side columns or scroll containers. Graph coordinates and navigation gestures SHALL NOT be persisted as learning records or interaction logs.

#### Scenario: See a current graph state

- **WHEN** a learner changes a knowledge-point state and refreshes the graph
- **THEN** the changed state is rendered from the workspace data

#### Scenario: Read coverage and closeness

- **WHEN** the graph contains nodes with different formal-problem counts and connected edges of different attraction
- **THEN** nodes with more formal problems are larger and stronger connected pairs settle at shorter target distances

#### Scenario: Navigate the graph directly

- **WHEN** the learner drags a node, pans the background, zooms, or fits the graph
- **THEN** the native canvas updates in memory and focused knowledge-point detail remains available in the outer right column

#### Scenario: Filter the visible graph

- **WHEN** the learner searches or filters by learning state
- **THEN** the remaining nodes are re-laid out and the simulation reheats without restoring removed nodes' coordinates as durable state

#### Scenario: Prefer reduced motion

- **WHEN** the browser reports `prefers-reduced-motion: reduce`
- **THEN** the graph computes a stable layout without progressive animation and paints the result once

#### Scenario: Inspect a focused node

- **WHEN** the learner focuses a graph node
- **THEN** the outer right detail tab presents its readable title, current state, related knowledge points, and safe editable fields

#### Scenario: Open the knowledge graph

- **WHEN** the learner clicks the knowledge graph navigation entry
- **THEN** the middle area displays the current chapter graph from the workspace data

#### Scenario: Graph artifact missing

- **WHEN** no rendered graph artifact exists on disk
- **THEN** the graph page remains available because it uses workspace data rather than the artifact

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

For each turn, the browser SHALL send object identifiers rather than page DOM, and the server SHALL rebuild authoritative workspace, course, chapter, route, page type, selected object, and relevant learning context from SQLite. Practice, knowledge-point, and graph pages SHALL respectively attach their defined object/state summaries. The latest three different browser-session object anchors SHALL also be attached. Unsubmitted answer and note drafts SHALL be excluded unless the learner explicitly enables the practice-only draft option for that turn.

#### Scenario: Ask about a knowledge point page

- **WHEN** the learner sends a turn from a knowledge-point page
- **THEN** the Agent receives current content, state, signals, schedule, neighbours, and related problems rebuilt from the workspace

#### Scenario: Keep a practice draft private

- **WHEN** an unsubmitted answer exists and the learner has not enabled draft attachment
- **THEN** the answer and note are absent from Agent context and are not persisted by the conversation bridge

#### Scenario: Attach a practice draft explicitly

- **WHEN** the learner enables draft attachment for a turn
- **THEN** only that turn receives the current answer draft in addition to the authoritative practice context

### Requirement: Learner-controlled daily conversation

Daily automatic conversation creation SHALL default off. When enabled, it SHALL use the browser's local date and create at most one conversation on the first workspace entry of that date, without interrupting a running conversation.

#### Scenario: Enter on a new local date with daily creation enabled

- **WHEN** no conversation was automatically created for that browser-local date and no turn is running
- **THEN** one new conversation is created with the learner's selected provider

