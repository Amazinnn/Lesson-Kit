## Purpose

The workbench UI is the minimal consumption surface of lesson-kit: a three-column
shell with a left navigation column (practice, knowledge points, knowledge
graph), a middle page area, a session-end self-rating step, and a right AI
conversation column whose context display prioritizes the current problem
without ever limiting what the agent can see. Visual style copies the DeepSeek
Harness design system.

## ADDED Requirements

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

The practice page SHALL present the practice flow as a message stream: problem
messages (rendered math), the learner's answer messages, solution-reveal
messages with the solution split into blocks, and a feedback box that appears
together with the reveal (1–5 rating, optional note, optional stuck-step
marker) that is never required. Problems SHALL be pulled from weak knowledge
points or a selected knowledge point list, auto-graded when the problem has
machine-gradable structure, and SHALL NOT repeat within the same session.

#### Scenario: Practice with reveal-then-feedback

- **WHEN** the learner submits an answer for an open problem and clicks "show answer"
- **THEN** the solution is revealed as blocks and a feedback box appears below the problem, and the learner can rate, note, mark a stuck step, or skip to the next problem

#### Scenario: No repeats in a session

- **WHEN** the practice page pulls problems during one session
- **THEN** no problem id appears twice in that session

### Requirement: Session-end unified self-rating

At the end of a practice session, the workbench SHALL show a minimal view
listing only the problems without feedback, with rating controls (1–5, optional
note), a skip-all action, and a single "practice similar" entry that pulls
problems for the same weak knowledge-point groups. The view SHALL NOT duplicate
problem content, answers, or any dashboard.

#### Scenario: Rate pending problems at session end

- **WHEN** the learner finishes a practice session with problems left unrated
- **THEN** the session-end view lists those problems with rating controls, and rating one records feedback and removes it from the list

#### Scenario: Practice similar from the session end

- **WHEN** the learner clicks the single "practice similar" entry
- **THEN** problems for the same weak knowledge-point groups are pulled and a new practice round starts

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

The knowledge point display page SHALL render the knowledge point body as
Markdown with LaTeX, wiki links (clickable, navigating to the linked knowledge
point), and figures, and SHALL show linked problems, signals with their cascade
reasons, and schedule state.

#### Scenario: Navigate a wiki link

- **WHEN** the learner clicks a wiki link in a knowledge point body
- **THEN** the display page navigates to the linked knowledge point

#### Scenario: See signal reasons

- **WHEN** the knowledge point has signals or cascade boosts
- **THEN** the display page shows the signal weight and the cascade reason text

### Requirement: Knowledge point list page

The knowledge point list page SHALL list the chapter's knowledge points
reachable from the left navigation entry, each linking to its display page, and
SHALL show the weak ordering with scores and cascade reasons.

#### Scenario: Open the knowledge point list

- **WHEN** the learner clicks the knowledge point navigation entry
- **THEN** the middle area lists the chapter's knowledge points in weak order, each linking to its display page

### Requirement: Knowledge graph page

The knowledge graph page SHALL display the chapter knowledge graph generated by
the existing graph renderer (or a clear generation hint when the artifact is
missing), reachable from the left navigation entry. The page SHALL be
display-only in v1.

#### Scenario: Open the knowledge graph

- **WHEN** the learner clicks the knowledge graph navigation entry and a rendered graph exists
- **THEN** the middle area displays the graph

#### Scenario: Graph artifact missing

- **WHEN** the learner clicks the knowledge graph navigation entry and no rendered graph exists
- **THEN** the page shows the generation command hint instead of a broken page
