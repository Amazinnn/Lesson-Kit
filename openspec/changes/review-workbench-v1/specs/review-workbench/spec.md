## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into weak-point-first daily practice,
with flexible feedback and a forgetting curve used as background guidance only.

## ADDED Requirements

### Requirement: Workspace registry

Each lesson-kit folder is a workspace. The registry maps a workspace name to a
folder path, its pool database, and its active course/chapter. A workspace can
be registered, listed, and opened (web shell or CLI), and a registered
workspace SHALL appear in the hub with its pool statistics.

#### Scenario: Register a folder as a workspace

- **WHEN** the user runs `wb init <path>` on a folder with lesson-kit structure (a `pool/*.db` file or `lessonkit.py`)
- **THEN** the folder is added to the registry under its folder name and the hub lists it with pool row counts

#### Scenario: List workspaces with statistics

- **WHEN** the hub page is loaded
- **THEN** it shows each registered workspace with course, chapter, knowledge-point count, problem count, due-item count, and weak-signal count

### Requirement: Weak knowledge point list

The workspace home SHALL list weak knowledge points ordered by a weakness score
derived from learner signals and due state. The score SHALL never filter items
out: everything stays reachable, ordering only prioritizes pain points.

#### Scenario: Weak points appear first

- **WHEN** a knowledge point has a high-weight learner signal and a due review
- **THEN** it is ordered above a knowledge point with no signal, regardless of due date

#### Scenario: Every knowledge point remains reachable

- **WHEN** the user searches or browses beyond the ordered weak list
- **THEN** all knowledge points of the course are still visible and selectable

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted, it SHALL fall back to `gate_passed`
candidates, and when both are exhausted it SHALL report the shortage per
knowledge point instead of inventing content.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered, with none repeated within the same session

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point and the UI offers the candidate-generation path instead of fabricating problems

### Requirement: Practice session

A practice session SHALL present one problem at a time with rendered math, record
a result (correct, wrong, stuck, skip), and persist each result to the pool
immediately. The schedule SHALL never block a problem from being practiced:
due dates are reminders, not locks.

#### Scenario: Answer a problem in a session

- **WHEN** the user submits a result for a problem
- **THEN** the attempt and updated progress are written to the pool and the next problem is shown

#### Scenario: Practice an un-due problem

- **WHEN** the user selects a problem that is not yet due
- **THEN** it is shown and practiced normally, with no lock or refusal

### Requirement: Reverse review from wrong results

After a wrong or stuck result, the session SHALL offer to practice the same
knowledge-point group again immediately, so the learner works the pain point
until it yields.

#### Scenario: Re-practice after a wrong answer

- **WHEN** a problem is answered wrong or stuck
- **THEN** the UI offers a "practice the same knowledge points again" action that pulls a fresh set for that group

### Requirement: Flexible feedback

Feedback SHALL be optional and free-form: a 1–5 self-rating, natural-language
notes, both, or neither. No form completion SHALL be required to continue a
session. Both forms SHALL be mapped to learner signals that influence future
weakness ordering, and the original note text SHALL be preserved verbatim.

#### Scenario: Rate mastery without text

- **WHEN** the learner gives a rating of 2 for a knowledge point without any note
- **THEN** the signal for that point is raised to high weight and the event is appended to the feedback log

#### Scenario: Describe a weakness in words

- **WHEN** the learner writes a natural-language note about a confusion
- **THEN** the note is mapped to a signal type, stored verbatim on the signal, and the event is appended to the feedback log

#### Scenario: Skip feedback entirely

- **WHEN** the learner submits a problem result without rating or note
- **THEN** the result is recorded and the session continues with no prompt or nag

### Requirement: Forgetting-curve scheduling as background

The system SHALL maintain per-item scheduling state (repetitions, ease,
interval, due date) updated on practice results, and SHALL surface due items as
reminders. Scheduling SHALL influence ordering only; it SHALL never hide,
lock, or refuse items.

#### Scenario: Due items are reminded

- **WHEN** the workspace home is opened
- **THEN** it shows a due-items summary computed from scheduling state, alongside (never instead of) the weak-point list

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the scheduling table

### Requirement: Session interruption recovery

All session state SHALL live in the pool, so closing the browser mid-session
loses nothing: reopening the workspace SHALL resume from the last recorded
state.

#### Scenario: Resume after closing the browser

- **WHEN** the user closes the browser mid-session and later reopens the workspace
- **THEN** recorded results are intact, the session summary reflects them, and practice can continue from the pool state
