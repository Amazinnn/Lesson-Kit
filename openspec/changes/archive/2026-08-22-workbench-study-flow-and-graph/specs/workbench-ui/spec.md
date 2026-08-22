## MODIFIED Requirements

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

### Requirement: Knowledge point display page

The knowledge point display page SHALL render linked problems grouped by their topic label. Each row SHALL present a concise problem title as its primary text and may show the raw problem id only as secondary context.

#### Scenario: Browse grouped linked problems

- **WHEN** a knowledge point has linked problems from multiple topics
- **THEN** the page displays separate labeled groups containing concise problem titles

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

The knowledge graph page SHALL render the current chapter graph from live workspace data inside the workbench rather than embedding a generated artifact. The middle column SHALL provide graph search, state filtering, zoom, and focus. The outer right column SHALL switch between knowledge-point detail and the existing AI teacher panel; the graph SHALL NOT render its own nested side columns or scroll containers.

#### Scenario: See a current graph state

- **WHEN** a learner changes a knowledge-point state and refreshes the graph
- **THEN** the changed state is rendered from the workspace data

#### Scenario: Inspect a focused node

- **WHEN** the learner focuses a graph node
- **THEN** the outer right detail tab presents its readable title, current state, related knowledge points, and safe editable fields

#### Scenario: Open the knowledge graph

- **WHEN** the learner clicks the knowledge graph navigation entry
- **THEN** the middle area displays the current chapter graph from the workspace data

#### Scenario: Graph artifact missing

- **WHEN** no rendered graph artifact exists on disk
- **THEN** the graph page remains available because it uses workspace data rather than the artifact
