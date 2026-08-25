## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into weak-point-first daily practice,
with flexible feedback and a forgetting curve used as background guidance only.
## Requirements
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

A workbench practice session SHALL present one problem at a time from a weak-point-first, non-repeating session queue. The learner SHALL choose either per-problem self-rating or end-of-session unified self-rating before the first problem is pulled. Showing a problem, drafting an answer, revealing a solution, skipping a problem, or ending a session without an explicit rating SHALL NOT write an attempt, feedback event, signal, progress row, or schedule update. The schedule SHALL never lock a problem.

#### Scenario: Skip a problem without a learning record

- **WHEN** the learner skips the current problem
- **THEN** the next unseen problem is shown and no learner-state table is changed

#### Scenario: Explicit rating records a learning conclusion

- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** the feedback, derived learner state, and schedule are persisted once

#### Scenario: Answer a problem in a session

- **WHEN** the learner completes a problem and explicitly submits a rating
- **THEN** the next unseen problem is shown after the single feedback write

#### Scenario: Practice an un-due problem

- **WHEN** the learner selects a problem that is not yet due
- **THEN** it is shown and practiced normally, with no lock or refusal

### Requirement: Reverse review from wrong results

After a wrong or stuck result, the session SHALL offer to practice the same
knowledge-point group again immediately, so the learner works the pain point
until it yields.

#### Scenario: Re-practice after a wrong answer

- **WHEN** a problem is answered wrong or stuck
- **THEN** the UI offers a "practice the same knowledge points again" action that pulls a fresh set for that group

### Requirement: Flexible feedback

Feedback SHALL consist of an optional natural-language note paired with an explicit 1–5 self-rating when the learner chooses to record a learning conclusion. A submitted rating SHALL preserve the note verbatim and update the existing signal and scheduling mechanisms. The workbench SHALL NOT request a feedback log for navigation or unfinished work.

#### Scenario: Rate mastery without text

- **WHEN** the learner submits a rating of 2 without a note
- **THEN** the corresponding knowledge-point signal is raised and one feedback event is appended

#### Scenario: Describe a weakness in words

- **WHEN** the learner submits a rating with a natural-language note about a confusion
- **THEN** the note is mapped to a signal type, stored verbatim on the signal, and one event is appended

#### Scenario: Skip feedback entirely

- **WHEN** the learner leaves a problem without submitting a rating
- **THEN** the session continues with no feedback, attempt, signal, progress, or schedule write

#### Scenario: Describe a weakness with a submitted rating

- **WHEN** the learner submits a rating and a natural-language note
- **THEN** the note is preserved verbatim and mapped through the existing signal rules

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

### Requirement: Grading input modes

Practice SHALL accept multiple answer and grading modes. Problems with machine-gradable structure (single choice, true/false) SHALL be graded automatically. Open text problems SHALL follow reveal-then-rate: the learner answers first (text or natural language), the solution is revealed, then the learner self-rates. If the learner declares no time to grade, the attempt SHALL be recorded without a grade and without blocking the session.

#### Scenario: Auto-grade a choice problem

- **WHEN** the learner selects an option for a machine-gradable problem
- **THEN** the system grades it correct or wrong and records the graded attempt

#### Scenario: Reveal-then-rate an open problem

- **WHEN** the learner submits text for an open problem
- **THEN** the solution is revealed, the learner self-rates, and the attempt records the answer text and the rating

#### Scenario: Record without grading

- **WHEN** the learner chooses "no time to grade"
- **THEN** the attempt is recorded with no grade and no rating, the schedule does not regress, and the session continues

### Requirement: Cascade signal boosts

Weak-point ordering SHALL combine evidence signals with query-time derived
boosts: a knowledge point with a signal boosts its related knowledge points
along `prerequisite` (the source is a prerequisite of the target), `applies_to`
(the source is the method used by the target), and `part_of` edges, in the
reverse direction, up to depth 2, decaying 0.5 per hop and weighted by relation
strength (high 1.0, medium 0.7, low 0.4). Derived boosts SHALL NEVER write to
`learner_signals` — that table stays evidence-only — and SHALL be shown with
their reason in the UI. `contrasts`, `variant_of`, and `generalizes` edges
SHALL NOT participate in cascading.

#### Scenario: Downstream weakness raises a prerequisite

- **WHEN** a knowledge point has a high-weight signal and a related prerequisite with no signal of its own
- **THEN** the prerequisite's ordering position rises due to the derived boost, and the UI states the reason ("raised because downstream X is weak")

#### Scenario: Cascades never fabricate evidence

- **WHEN** ordering is computed with derived boosts active
- **THEN** no `learner_signals` row is created or modified by the derivation, and a knowledge point with neither evidence nor any downstream neighbor keeps its base ordering

### Requirement: Step-level stuck marking

For open-ended or multi-step problems, the practice page SHALL present the
solution as blocks and let the learner mark "stuck at block N" with an optional
natural-language note. The marking SHALL be recorded on the attempt (note and
answer text) and SHALL be included in the context of any later explain or
diagnose task for that problem. Marking is never required.

#### Scenario: Mark a stuck step in a proof

- **WHEN** the learner marks "stuck at step 3" with a short note on a proof problem
- **THEN** the attempt records the step marker and note, and a later diagnose task for that problem carries the marker in its context

### Requirement: Directional card practice for memory recall

A knowledge point with `knowledge_type = memory-recall` SHALL be practiced as a
card: prompt on the front, recall, reveal on the back. Cards SHALL carry a
direction (for example English-to-Chinese and Chinese-to-English), each
direction is a distinct learning action with its own schedule entry, and
related knowledge points connected by `contrasts` or `variant_of` edges SHALL
be shown alongside during card practice.

#### Scenario: Two directions schedule independently

- **WHEN** a memory-recall knowledge point is practiced in both directions
- **THEN** each direction has its own schedule state and due date, and practicing one direction does not advance the other

#### Scenario: Confusable words are shown together

- **WHEN** a card's knowledge point has a `contrasts` neighbor
- **THEN** the neighbor is displayed on the card page as a compare hint, without merging the two into one item

### Requirement: Answer text capture for open problems

The practice page SHALL provide an answer box for open problem types (proof,
design, modeling, explanation, application) and SHALL store the learner's text
on the attempt. The latest attempt's answer text SHALL be included in the
context of a diagnose task for that problem.

#### Scenario: Attach a design attempt to its record

- **WHEN** the learner pastes their own design into the answer box and submits a result
- **THEN** the attempt stores the answer text, and a diagnose task started for that problem includes it

### Requirement: Past-paper coverage gate

Extraction inputs SHALL include past exam papers, and a machine-readable
coverage contract (`01_inputs/past-paper-coverage.json`) SHALL map every exam
point to a pool knowledge point or durable problem. The coverage gate SHALL
fail with the list of unmapped exam points when any point lacks a mapping, and
the workbench SHALL surface unmapped exam points as pool gaps eligible for the
candidate-generation path.

#### Scenario: Every exam point is mapped

- **WHEN** the coverage gate runs and all exam points map to pool items
- **THEN** the gate passes and no gap is reported

#### Scenario: An exam point is unmapped

- **WHEN** an exam point has no mapping to any knowledge point or durable problem
- **THEN** the gate fails, the unmapped point is listed, and the workbench shows it as a pool gap with a candidate-generation entry point

### Requirement: Current learning state

The workbench SHALL maintain one current state for each knowledge point or problem, selected from `needs_work`, `review`, and `mastered`. A submitted rating of 1–2, 3–4, or 5 SHALL respectively set that state. A learner's explicit graph-state edit SHALL replace only the current state and update scheduling through the corresponding rating without appending a feedback event or learner signal.

#### Scenario: Edit a graph state without creating a history event

- **WHEN** the learner changes a knowledge point from review to mastered in the graph
- **THEN** the current state and schedule are updated and feedback-event and learner-signal counts do not increase

### Requirement: Semantic graph attraction

The live graph model SHALL expose each knowledge point's formal-problem count and each semantic edge's explicit strength, shared-formal-problem count, and computed attraction. Edges SHALL originate only from formal knowledge relations or existing `related_kp_ids`. Reverse duplicate edges SHALL be merged, and shared problems SHALL reinforce but SHALL NOT create semantic edges.

#### Scenario: Count formal problems per node

- **WHEN** formal and candidate problems refer to the same knowledge point
- **THEN** `problem_count` includes only formal problems

#### Scenario: Merge a bidirectional semantic edge

- **WHEN** two knowledge points relate to each other through duplicate or reverse relation declarations
- **THEN** the graph model returns one edge for that unordered pair

#### Scenario: Reinforce an existing relation with shared problems

- **WHEN** two related knowledge points share formal problems
- **THEN** their edge reports the shared count and higher computed attraction

#### Scenario: Do not infer a relation from co-occurrence

- **WHEN** two knowledge points share a problem but have no formal relation or `related_kp_ids` link
- **THEN** the graph model returns no edge between them
