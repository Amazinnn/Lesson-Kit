## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into **Paper assembly** and Paper-backed
Practice Runs. Weakness evidence, due state, scope, and source filters guide how a
Paper is assembled; once a Practice Run starts, its ordered Paper items are fixed.
Flexible feedback and forgetting-curve scheduling remain background guidance only.
## Requirements
### Requirement: Workspace registry

Each lesson-kit folder is a workspace. The registry maps a workspace name to a
folder path, its pool database, and its active course/chapter. A workspace can
be registered, listed, and opened (web shell or CLI), and a registered
workspace SHALL appear in the hub with its pool statistics. Hub statistics
SHALL be counted over the workspace's whole course pool — every chapter present
in that pool — regardless of the active chapter lens.

A workspace SHALL register exactly one pool database, and that database SHALL
live inside the workspace folder. Registration SHALL ignore ingest backups
(`*.db.ingest-backup`, `pool/backups/*`) when choosing the pool, SHALL refuse a
folder whose remaining candidates are several databases unless one of them is the
explicitly named course, and SHALL refuse to register a folder or a database that
another registered workspace already owns. Re-registering the same name for a
different folder SHALL be refused instead of silently replacing the existing
entry. The active chapter SHALL be an identifier (lowercase ASCII letters, digits,
and dashes) or empty, and a value that is not SHALL be refused with the reason.

#### Scenario: Register a folder as a workspace

- **WHEN** the user runs `lesson-kit init <path>` on a folder with lesson-kit structure (a `pool/*.db` file or `lessonkit.py`)
- **THEN** the folder is added to the registry under its folder name and the hub lists it with pool row counts

#### Scenario: List workspaces with statistics

- **WHEN** the hub page is loaded
- **THEN** it shows each registered workspace with its course, chapter, knowledge-point count, problem count, due-item count, and weak-signal count, all counted course-wide

#### Scenario: Hub statistics ignore the chapter lens

- **WHEN** the active chapter lens selects a chapter that holds only part of the pool
- **THEN** the hub card still reports course-wide counts and does not shrink to the selected chapter

#### Scenario: A backup is never adopted as the pool

- **WHEN** a folder holds both a live pool and an ingest backup (or a pre-readiness copy of the pool)
- **THEN** registration selects the live pool and the backup file is left untouched

#### Scenario: Several pools ask which one

- **WHEN** a folder holds more than one candidate pool database and none matches the named course
- **THEN** registration fails and lists the candidates with the command that selects one

#### Scenario: Two workspaces cannot share a pool

- **WHEN** a folder whose pool database is already registered under another workspace name is registered again
- **THEN** the registration is refused and both existing entries stay intact

#### Scenario: A name collision does not silently replace

- **WHEN** `init` runs with a name that is already registered for a different folder
- **THEN** the existing registration is left unchanged and the command fails with the conflict

#### Scenario: An invalid chapter is refused

- **WHEN** a chapter value that is not a lowercase ASCII identifier is passed to `init` or `use`
- **THEN** nothing is stored and the error explains the accepted form

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

### Requirement: Paper assembly engine

The pull engine SHALL assemble the ordered problem portion of a Paper from an
explicit knowledge-point scope, conditional source/difficulty filters, and
learner evidence such as weak, due, or previously wrong items. Assembly SHALL be
a read operation with zero learning writes. When durable problems are exhausted,
it SHALL report the shortage per knowledge point instead of inventing content.
Every selected problem SHALL carry the reason it entered the Paper.

Exact problem ids supplied by an Agent or CLI authoring workflow SHALL be
included in the Paper when they resolve to existing durable problems, with
reason `explicit`, even when they fall outside the requested scope or filters or
exceed the requested problem count. This exact-id capability is an authoring
primitive, not a learner-facing practice control: the browser SHALL NOT expose a
per-problem picker or scope/filter/quantity assembly controls. Browser Paper-list management SHALL not edit item membership or order; authoring through Agent/CLI remains available.

#### Scenario: Assemble a Paper for one weak knowledge point

- **WHEN** the learner asks the Agent to use one weak knowledge point as the requested practice scope
- **THEN** the engine assembles durable problems for a Paper constrained to that scope and reports the selection reasons before execution begins

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested for the Paper
- **THEN** the assembly result lists the shortfall per knowledge point and points to the Check pipeline instead of fabricating problems

#### Scenario: Agent pins an exact problem while authoring

- **WHEN** an Agent or CLI authoring workflow supplies an exact id for an existing durable problem while composing a Paper
- **THEN** the Paper SHALL include that problem with reason `explicit`, even if it falls outside the requested scope or filters or exceeds the requested problem count, without creating a learner-side manual-pick affordance

#### Scenario: Learner evidence guides assembly

- **WHEN** Paper assembly is driven by weak knowledge points, due problems, or previously wrong problems
- **THEN** the returned problems reflect that evidence and each carries the matching reason

### Requirement: Paper-backed Practice Run
A Practice Run SHALL execute one already determined Paper and preserve its ordered item identities. Viewing, answering, skipping, rating, scheduling or Agent discussion SHALL NOT dynamically pull extra items into it. At most one selected active run exists per workspace execution resource, but each saved Paper MAY retain its own unfinished execution independently. Switching selection SHALL pause rather than abandon the previous Paper and SHALL NOT require completing it first. Only explicit governed content edits/deletion under this change may alter or reset unfinished execution state; those are not scheduler-driven assembly.

A Paper SHALL NOT be defined by one product-level content-mode choice. Each item SHALL use its actual validated answering type. Existing `practice_mode` fields MAY remain compatibility metadata but SHALL NOT force every item into the same form or recreate a dynamic queue. Self-rating preference controls learning feedback only; Answer Reveal Timing separately controls result disclosure and answer locking. Displaying, drafting, revealing, skipping or ending work SHALL NOT manufacture learning evidence. Scheduling SHALL never lock an item.

#### Scenario: Start from an assembled Paper
- **WHEN** a Paper's ordered items are fixed and the learner starts it
- **THEN** those exact items become the Practice Run and no later scope or scheduler change mutates it

#### Scenario: Skip an item without a learning record
- **WHEN** the learner skips the current item without an explicit recorded conclusion
- **THEN** execution advances by the existing skip rules and no learner-state row is manufactured

#### Scenario: Explicit rating records a learning conclusion
- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** feedback, derived learner state and schedule persist exactly once

#### Scenario: Off-mode verdict remains compatible
- **WHEN** an objective item uses compatibility rating mode `off`
- **THEN** its recorded verdict derives the existing learning conclusion exactly once without synthesizing a rating event

#### Scenario: Agent records only at the learner's request
- **WHEN** the learner asks the Agent to record the active answer
- **THEN** only the explicit attempt command records it; viewing or discussing the draft alone does not

#### Scenario: Switch between unfinished Papers
- **WHEN** Paper A is partly completed and the learner starts or resumes Paper B, then returns to A
- **THEN** both retain independent unfinished progress, A resumes its own cursor/items/drafts, and no run is marked abandoned or completed merely by switching

### Requirement: Durable practice run archive

The single active-practice resource SHALL remain the execution authority for one
Paper-backed Practice Run. Every newly created execution SHALL use the product
source semantic `paper`; historical `quick`, `practice_set`, or `agent` source
values MAY remain readable as migration data, and replaying such history SHALL
create a new Paper-sourced execution from the archived fixed items.

When the learner explicitly submits the Paper, or a run is explicitly replaced or cleared, the workbench SHALL
append one minimal `practice_runs` snapshot before deleting active execution
state. The snapshot SHALL preserve Paper source identity/reference/label, ordered
item identities and final states, rating compatibility metadata, timestamps, and the submitted per-item answer references and presentation state needed to reopen the completed answer sheet. It SHALL NOT replace, duplicate, edit, or delete `problem_attempts` or
`feedback_events`.

#### Scenario: Completing the last item archives the run

- **GIVEN** the learner has explicitly requested final Paper submission
- **WHEN** the final pending item of an active Paper is answered or marked stuck
- **THEN** one completed snapshot is appended and active execution is cleared exactly once as part of that explicit submission
- **AND** answering the last item outside explicit final submission does not archive the run

#### Scenario: Replacing an unfinished run keeps both histories honest

- **WHEN** the learner explicitly replaces an unfinished Paper run
- **THEN** the old run is archived as abandoned, its existing attempts remain unchanged, and the new Paper starts independently

#### Scenario: Replay legacy history through the Paper boundary

- **WHEN** a historical run labelled `quick`, `practice_set`, or `agent` is replayed
- **THEN** its archived item order is reused but the new active execution stores the Paper source semantic

### Requirement: Re-assembly after wrong results

A wrong or stuck result MAY be discussed with the Agent to request authoring a new Paper from relevant knowledge scope or learning evidence. It SHALL NOT expose a learner-operated assemble-similar button. The completed or
running Paper SHALL never be extended in place, and the follow-up SHALL not
silently inherit an old seen-id queue as its execution identity.

#### Scenario: Build a follow-up Paper after a wrong answer

- **WHEN** a problem is answered wrong or stuck and the learner asks the Agent to author similar material
- **THEN** Lesson Kit assembles a new Paper from the relevant scope/evidence and starts it only after its item list is determined

### Requirement: Flexible feedback

Feedback SHALL preserve a natural-language note and optional 1–5 learning
rating. A learner self-rating or a learner-requested Agent rating MAY record a
learning conclusion. A rating SHALL use the same signal and schedule rules,
independent of who submitted it. Navigation and unfinished work SHALL NOT
request or create a feedback log.

#### Scenario: Rate mastery without text

- **WHEN** the learner submits a rating of 2 without a note
- **THEN** the corresponding knowledge-point signal is raised and one feedback event is appended

#### Scenario: Describe a weakness in words

- **WHEN** the learner submits a rating with a natural-language note about a confusion
- **THEN** the note is preserved verbatim, mapped through existing signal rules, and one event is appended

#### Scenario: Skip feedback entirely

- **WHEN** the learner leaves a problem without submitting a rating or requesting Agent recording
- **THEN** the session continues without a new feedback, attempt, signal, progress, or schedule write

#### Scenario: Describe a weakness with a submitted rating

- **WHEN** the learner submits a rating and a natural-language note
- **THEN** the note is preserved verbatim and mapped through the existing signal rules

### Requirement: Forgetting-curve scheduling as background

The system SHALL maintain per-item scheduling state (repetitions, ease,
interval, due date) updated on recorded practice results. Scheduling SHALL
influence ordering, suggestions, and Paper Assembly only; it SHALL never hide,
lock, refuse, or inject items into an already running Paper. Due items SHALL NOT
be surfaced as a standing due list or through a separate review page.

Due knowledge points MAY appear as on-demand practice suggestions with at most
one human-readable reason phrase. Acting on such a suggestion SHALL establish or
prefill a Paper-assembly scope; it SHALL NOT add a knowledge point or problem to
a staged execution queue.

#### Scenario: Due items are suggested for Paper assembly

- **WHEN** due schedule rows exist for knowledge points outside the learner's current assembly scope
- **THEN** the practice departure surface can suggest those points with one human reason phrase and an action to assemble from them, never raw scheduler parameters

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the scheduling table without mutating the running Paper

### Requirement: Practice Run interruption recovery
Recorded learning conclusions SHALL remain durable. Each saved Paper's unfinished checkpoint SHALL durably preserve source identity, fixed ordered items, cursor, Answer Reveal Timing, submission locks, reference-view facts, stuck marks, completion states, self-ratings and unsubmitted answer/choice drafts across navigation, refresh and browser/service restart. Selecting another Paper SHALL NOT clear it. Draft persistence SHALL NOT create an attempt, verdict, feedback, signal, learning-progress or schedule entry. Submitted evidence and completed historical runs SHALL NOT be reconstructed from drafts or markers.

#### Scenario: Resume the same Paper after refresh
- **WHEN** the learner refreshes or leaves and returns to an unfinished Paper
- **THEN** its own fixed items, execution progress and unsubmitted answer/choice drafts are restored without repeating assembly

#### Scenario: Recorded results survive browser closure
- **WHEN** the learner closes the browser after recording results and reopens the workspace later
- **THEN** recorded results and every saved Paper's surviving unfinished checkpoint remain available, with only the selected Paper active

#### Scenario: Unsubmitted browser state creates no record
- **WHEN** the tab ends with an unsubmitted draft, note, reveal state or rating
- **THEN** no learning evidence is fabricated; supported inputs and presentation state are preserved as execution state only, and already confirmed ratings remain durable

### Requirement: Grading input modes

Machine-gradable choice and true/false content SHALL retain its existing
automatic verdict. Open problems SHALL continue to support answer, reveal,
then learner self-rating. The learner MAY instead ask an Agent to transcribe
and grade the answer through the attempt CLI. An answer whose learning rating
cannot be determined MAY be recorded without a rating and SHALL NOT regress
the schedule.

#### Scenario: Auto-grade a choice problem

- **WHEN** the learner selects an option for a machine-gradable problem
- **THEN** the system grades it correct or wrong and records the graded attempt

#### Scenario: Reveal-then-rate an open problem

- **WHEN** the learner submits text for an open problem
- **THEN** the solution is revealed, the learner self-rates, and the attempt records the answer text and rating

#### Scenario: Record without grading

- **WHEN** the learner or Agent records an answer without a learning rating
- **THEN** the attempt is retained without changing signals, current states, progress, or schedule

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
natural-language note. The marking SHALL be recorded on the explicit attempt
and SHALL be available in authoritative Agent conversation context for that
problem. Marking is never required.

#### Scenario: Mark a stuck step in a proof

- **WHEN** the learner records "stuck at step 3" with a short note on a proof problem
- **THEN** the attempt stores the marker and note and later Agent context for that problem includes them

### Requirement: Answer text capture for open problems

The practice page SHALL provide an answer box for open problems. A learner's
explicit rated submission or learner-requested Agent attempt CLI call SHALL
store the answer text. The latest recorded answer SHALL be available to later
authoritative Agent context. Unsubmitted drafts SHALL remain unwritten.

#### Scenario: Attach a design attempt to its record

- **WHEN** the learner submits a design answer with an explicit rating
- **THEN** the attempt stores the answer text and later Agent context includes it

#### Scenario: Agent transcribes a photographed answer

- **WHEN** the learner asks the Agent to record a photographed open answer
- **THEN** later Agent context can read the transcription without a stored answer-image attachment

### Requirement: Past-paper coverage gate

Extraction inputs SHALL include past exam papers, and a machine-readable
coverage contract (`01_inputs/past-paper-coverage.json`) SHALL map every exam
point to a pool knowledge point or durable problem. The coverage gate SHALL
fail with the list of unmapped exam points when any point lacks a mapping, and
the workbench SHALL surface unmapped exam points as pool gaps eligible for the
Check ingest path.

#### Scenario: Every exam point is mapped

- **WHEN** the coverage gate runs and all exam points map to pool items
- **THEN** the gate passes and no gap is reported

#### Scenario: An exam point is unmapped

- **WHEN** an exam point has no mapping to any knowledge point or durable problem
- **THEN** the gate fails, the unmapped point is listed, and the workbench shows it as a pool gap with a Check ingest entry point

### Requirement: Current learning state

The workbench SHALL maintain one current state for each knowledge point or problem, selected from `needs_work`, `review`, and `mastered`. A submitted rating of 1–2, 3–4, or 5 SHALL respectively set that state. A learner's explicit graph-state edit SHALL replace only the current state and update scheduling through the corresponding rating without appending a feedback event or learner signal.

#### Scenario: Edit a graph state without creating a history event

- **WHEN** the learner changes a knowledge point from review to mastered in the graph
- **THEN** the current state and schedule are updated and feedback-event and learner-signal counts do not increase

### Requirement: Semantic graph attraction

The live graph model SHALL expose each knowledge point's formal-problem count
and importance and each semantic edge's explicit strength, shared-formal-
problem count, and computed attraction. Only formal problems contribute to
problem counts. Edges originate only from formal relations or existing
`related_kp_ids`; co-occurrence never invents an edge.

#### Scenario: Count formal problems per node

- **WHEN** formal problems refer to a knowledge point
- **THEN** `problem_count` includes those formal problems and no retired candidate source

#### Scenario: Merge a bidirectional semantic edge

- **WHEN** two knowledge points declare duplicate or reverse semantic relations
- **THEN** the graph model returns one edge for the unordered pair

#### Scenario: Reinforce an existing relation with shared problems

- **WHEN** two related knowledge points share formal problems
- **THEN** their edge reports the shared count and higher computed attraction

#### Scenario: Do not infer a relation from co-occurrence

- **WHEN** two knowledge points share a problem but have no formal relation
- **THEN** the graph model returns no edge between them

### Requirement: Unified Agent data CLI

The workbench SHALL expose JSON data commands for get, list, search, history,
create, update, delete, and current-state replacement across knowledge points,
formal problems, and knowledge relations. Read operations SHALL perform zero
writes. Candidate entities, candidate gates, and candidate promotion SHALL NOT
exist; governed content enters through the Check pipeline.

#### Scenario: Search without a write

- **WHEN** an Agent searches the pool through `lesson-kit data`
- **THEN** matching current entities are returned and no content or learning row changes

#### Scenario: Candidate command is unavailable

- **WHEN** an Agent requests a candidate entity or promotion command
- **THEN** the CLI rejects the unsupported entity/action instead of recreating candidate state

#### Scenario: Edit a candidate

- **WHEN** an Agent requests an update for a retired candidate entity
- **THEN** the CLI rejects the unsupported entity and no pool row changes

#### Scenario: Promote a gated candidate

- **WHEN** an Agent requests retired candidate promotion
- **THEN** the CLI rejects the unsupported action and points to the Check pipeline

### Requirement: Readable content sequences

New knowledge points, formal problems, relations, and ingest batches SHALL use
course/chapter-scoped sequential readable identifiers. Existing suffixes seed
the next value; no hash-derived identifier is used.

#### Scenario: Allocate after existing content

- **WHEN** a scope already contains numbered entities and a new entity is created
- **THEN** it receives the next readable number without reusing a deleted id

### Requirement: Action-oriented learning reminders

Student-facing surfaces SHALL NOT expose raw signal types, weights, weakness scores, scheduler state, repetitions, ease, or manual three-state mastery controls. An item with explicit current weakness evidence SHALL display `重点练习`; otherwise an item that is due SHALL display `可以复习`; all other items SHALL remain neutral. The underlying evidence, scheduling, and compatibility APIs SHALL remain available to ordering and Agent context.

#### Scenario: Show an explicit weakness action

- **WHEN** a knowledge point has current explicit weakness evidence
- **THEN** its student-facing reminder is `重点练习` without raw signal or scheduler parameters

#### Scenario: Show only a due reminder

- **WHEN** an item has no current explicit weakness evidence and is due
- **THEN** its student-facing reminder is `可以复习` without claiming mastery

#### Scenario: Keep an unevidenced item neutral

- **WHEN** an item has neither current weakness evidence nor a due review
- **THEN** no mastery claim or internal state label is shown

### Requirement: Formal problems are reveal-ready

Every formal problem eligible for practice SHALL have a non-empty gated solution. A formal pool update SHALL NOT expose a partially solved batch.

#### Scenario: Reveal a formal problem solution

- **WHEN** the learner reveals any formal problem in the active pool
- **THEN** a non-empty solution that passed the formal content gates is available

### Requirement: Directional schedule entries

Each direction (for example English-to-Chinese and Chinese-to-English) of a
memory-recall knowledge point SHALL be a distinct learning action with its own
schedule entry, and practicing one direction SHALL NOT advance the other. The
workbench SHALL NOT provide a standing card-session page or system-initiated
card prompts; card-shaped UI for directional rows is deferred until real usage
exists.

#### Scenario: Two directions schedule independently

- **WHEN** a memory-recall knowledge point is practiced in both directions
- **THEN** each direction has its own schedule state and due date, and
  practicing one direction does not advance the other

#### Scenario: No system-initiated card session

- **WHEN** the learner starts any practice mode with due directional rows in
  scope
- **THEN** the workbench starts the requested mode directly without offering
  or requiring a card session

### Requirement: Browser manual include filter is retired

`include_ids` SHALL NOT be a learner-facing browser practice capability. Browser
`POST /pull` callers that send it SHALL be refused rather than silently changing
which concrete problems enter a Practice Run. Exact problem selection remains
available only through the explicit Agent/CLI Paper-authoring primitive (for
example `--problem`) and SHALL occur before the Paper starts.

Low-level or historical CLI compatibility code MAY continue to understand a
scoped include filter during migration, but live product documentation and new
UI behavior SHALL NOT treat it as a practice control.

#### Scenario: Stale browser caller sends include ids

- **WHEN** a browser practice pull carries `include_ids`
- **THEN** the request is rejected with an explicit migration message and no Practice Run is changed

#### Scenario: Agent pins a problem through Paper authoring

- **WHEN** an Agent needs one known problem in a Paper
- **THEN** it uses the exact-problem authoring path before execution rather than the retired browser include filter

### Requirement: Directional feedback key

Feedback MAY carry an optional `direction`; when present, the rating SHALL
update the schedule row keyed by `(item_type, item_id, direction)` while
signal, event, progress, and current-state semantics SHALL remain unchanged.

#### Scenario: Reverse card rating

- **WHEN** feedback for a knowledge point carries `direction: reverse` with
  rating 4
- **THEN** only the reverse schedule row advances and the forward row stays
  unchanged

### Requirement: Unified CLI entry point

The workbench SHALL expose its super CLI under the single command name
`lesson-kit`; `python -m workbench.cli.main` SHALL be an equivalent module form
of the same CLI. The
CLI serves two audiences over one implementation: a small, stable human surface
(init, use, dashboard, daemon, ls, bridge, doctor) and an agent surface (data,
pull, practice, feedback, ingest, goals). The human surface SHALL stay
parameter-light: beyond the subcommand name, a human command SHALL require at
most two parameters, SHALL default or derive every value it can infer, and when
it cannot infer a required value it SHALL fail with a ready-to-paste complete
command instead of a bare argument error. A human command that reports learning
data SHALL keep its human-readable default and SHALL also accept a flag that
makes the same data machine-readable, so an Agent is never forced to parse prose.
`lesson-kit init [path]` SHALL
register a workspace, with the path defaulting to the
current directory; when the folder is not yet a lesson-kit workspace, it SHALL
instead create one — pool database, `.lessonkit/` skeleton — without modifying
existing data. The course **identifier** (the prefix of every content id and the
pool file name) is separate from the workspace name: the name stays whatever the
user or the folder gives it, while the identifier SHALL come from, in order, an
explicit `--course`, else the pool database name of an already-initialized
workspace, else the folder name when that name is ASCII-safe (lowercased, runs of
non-alphanumeric characters folded to `-`), else an automatically allocated
sequential short code (`c01`, `c02`, …) that no registered workspace has used.
An explicit `--course` SHALL be a lowercase ASCII slug, and a value that is not
SHALL be rejected with the reason rather than stored.
`lesson-kit dashboard` SHALL ensure the local workbench service is
running and open the workbench in the browser; it SHALL NOT introduce a fourth
workbench page or reinterpret the existing three-page shell.

#### Scenario: Register a workspace through the lesson-kit command

- **WHEN** the user runs `lesson-kit init <path> --course <course> --chapter <chapter>`
- **THEN** the folder is registered with that course and chapter and appears in the hub, and the same registration is reachable as `python -m workbench.cli.main init`

#### Scenario: Open the dashboard

- **WHEN** the user runs `lesson-kit dashboard` while no service is running
- **THEN** the service is started in the background, the workbench URL is opened in the browser, and the command reports success only after the service actually answers

#### Scenario: Create a workspace from an empty folder

- **WHEN** the user runs `lesson-kit init <empty-folder> --course <course>`
- **THEN** a pool database for that course, the `.lessonkit/` skeleton directories, and the registry entry are created, and the folder appears in the hub without any other setup step

#### Scenario: Initializing an existing workspace never rewrites it

- **WHEN** the user runs `lesson-kit init` on a folder that is already a lesson-kit workspace
- **THEN** only registration runs, and no pool or skeleton file is created or overwritten

#### Scenario: Initialize from the current directory

- **WHEN** the user runs `lesson-kit init --course <course>` inside a course folder that is not yet a workspace
- **THEN** that folder is initialized and registered exactly as `lesson-kit init . --course <course>` would, and the command prints no argument error

#### Scenario: Course derived from a folder name

- **WHEN** the user runs `lesson-kit init` inside a folder whose name is ASCII, with no `--course` and no pool database
- **THEN** the course slug is the lowercased folder name with non-alphanumeric runs folded to `-`, and the pool database is created under that name

#### Scenario: A folder name that cannot yield a slug asks for one

- **WHEN** the user runs `lesson-kit init` inside a folder whose name is not ASCII, with no `--course` and no pool database
- **THEN** nothing is asked for: the folder is initialized with an automatically allocated sequential course code, the workspace name stays the folder name, and no argument error is printed

#### Scenario: Automatic codes do not repeat

- **WHEN** another such folder is initialized after one already holds the first automatic code
- **THEN** the new workspace receives the next code in the sequence

#### Scenario: An explicit course must be a slug

- **WHEN** the user runs `lesson-kit init --course <value>` with a value that is not a lowercase ASCII slug
- **THEN** nothing is created and the error explains that the course prefixes every content id

#### Scenario: Already-initialized folder needs no course

- **WHEN** the user runs `lesson-kit init` inside a folder that already contains a pool database and is not registered
- **THEN** the course is taken from that database's name and the folder is registered without a `--course` flag

#### Scenario: A read command serves both audiences

- **WHEN** the Agent asks the weak-point, due, or workspace-stats command for machine-readable output
- **THEN** the same data is printed as JSON, and the default human output for that command is unchanged

### Requirement: Background workbench service

The workbench service SHALL be startable, stoppable, and reportable from the
CLI without blocking the caller's terminal. The service SHALL remain a single
instance on the fixed local port, and its process id and log SHALL be recorded
under the same user-level registry directory that holds workspaces and bridge
configuration. The CLI SHALL NOT report a successful start when the service is
not actually serving, and SHALL NOT claim a running service when its recorded
process is gone.

#### Scenario: Start the background service

- **WHEN** the user runs `lesson-kit daemon start`
- **THEN** the service is running detached, its process id is recorded, and the command returns after confirming the port answers

#### Scenario: Starting twice keeps one service

- **WHEN** the user runs `lesson-kit daemon start` while a service is already running
- **THEN** no second service is started and the command reports the existing one

#### Scenario: Stop the background service

- **WHEN** the user runs `lesson-kit daemon stop` while the service is running
- **THEN** the service process is terminated, its recorded process id is cleared, and the port is released

#### Scenario: Report a service that is not running

- **WHEN** the user runs `lesson-kit daemon status` with no service running
- **THEN** it reports that nothing is running rather than an error traceback

### Requirement: Course and chapter switching

The active chapter SHALL act as a course-wide view lens with two writers over
one registry value: the dashboard chapter switch (the human surface) and
`lesson-kit use <course> <chapter>` (the agent-and-script surface). An empty
chapter SHALL explicitly mean the whole course, with no chapter filter. A
switch SHALL NOT create, move, or delete any data; subsequent page and prefix
queries SHALL resolve against the new lens; and no pool file SHALL be modified.
When several workspaces are registered, the workspace SHALL be selectable
explicitly. An unknown workspace or a missing argument SHALL be reported as an
error without changing stored state. A course value that is not a lowercase
ASCII slug SHALL be rejected with the reason, since it prefixes every content
id.

#### Scenario: Switch the active chapter from the dashboard

- **WHEN** the learner turns the chapter switch on and selects a chapter in the top bar
- **THEN** subsequent views and practice resolve against that chapter and the registry records it as the active chapter

#### Scenario: Turn the lens off

- **WHEN** the learner turns the chapter switch off
- **THEN** views and practice resolve against the whole course pool and the registry records an empty active chapter

#### Scenario: Switch the active chapter

- **WHEN** the user runs `lesson-kit use <new-course> <new-chapter>`
- **THEN** subsequent hub, page, and prefix queries resolve against the new course and chapter, and no pool file was modified

#### Scenario: Switch to the whole course from the CLI

- **WHEN** the user runs `lesson-kit use <new-course> ""`
- **THEN** the registry records an empty active chapter and views resolve against the whole course pool

#### Scenario: Switching never happens silently on error

- **WHEN** the user names a workspace that is not registered or omits an argument
- **THEN** the command fails with a clear message and the registry is unchanged

#### Scenario: A chapter that is not an identifier is refused

- **WHEN** a chapter value that is not a lowercase ASCII identifier is passed to `use`
- **THEN** nothing is stored and the error explains the accepted form

### Requirement: Environment self-check

The CLI SHALL provide a read-only `doctor` command that reports, in one run:
whether the workspace registry is readable, whether each registered
workspace's pool database exists and opens, whether each discovered provider's
resolved executable exists, whether the background service is running and its
port answers, and whether per-workspace runtime files (goals, plan) parse. The
command SHALL write nothing and change nothing. It SHALL exit zero only when
every check passes, and otherwise exit nonzero with each failed check listed.

#### Scenario: A healthy machine passes cleanly

- **WHEN** `lesson-kit doctor` runs with a readable registry, existing databases, existing provider executables, and no failures
- **THEN** every check is reported and the exit code is zero

#### Scenario: A broken setup is listed, not guessed

- **WHEN** a registered workspace's database file is missing, or a provider's resolved executable no longer exists
- **THEN** the failing check is reported by name with the offending path, nothing is repaired automatically, and the exit code is nonzero

#### Scenario: Doctor never mutates state

- **WHEN** `lesson-kit doctor` runs in any state, healthy or broken
- **THEN** no registry entry, database, or runtime file is created, modified, or deleted

### Requirement: Encoded names resolve in workbench routes

Every workbench route that carries a workspace name or a file path in its URL
SHALL decode percent-encoded path segments before looking the workspace up in
the registry or resolving a path on disk — the page shell, the JSON API, the
figure route, and the graph-artifact route alike. A workspace whose name
contains non-ASCII characters or spaces SHALL therefore open normally in the
browser and answer its API calls, and an unknown name SHALL still produce a
404 rather than a server error.

#### Scenario: A name with non-ASCII characters opens

- **WHEN** a workspace is registered under a name containing non-ASCII characters and the browser requests that workspace's practice page
- **THEN** the page renders for that workspace instead of returning 404

#### Scenario: Encoded names reach the API

- **WHEN** the browser percent-encodes a non-ASCII workspace name in an API request
- **THEN** the API resolves that workspace and answers as it does for an ASCII name

#### Scenario: Unknown names still fail cleanly

- **WHEN** a request names a workspace that is not registered
- **THEN** the route answers 404 and does not raise a server error

### Requirement: Workspace file containment

Every file path a workbench operation builds for a workspace SHALL resolve inside
that workspace's folder. Workspace data — pool database, `.lessonkit/` figures and
jobs, plan and goal files — SHALL be read and written through paths derived from
the registered folder; a value that arrives from a client (page route segment, API
body, artifact manifest) SHALL be validated as a plain name before it becomes a
path segment: no path separator, no `..`, no absolute path, no drive letter.
Conversation and turn identifiers SHALL additionally match their generated shape
(`conv-NNN`, `turn-NNN`). A value that fails validation SHALL be reported as an
error and SHALL cause no read, write, or deletion outside the workspace folder; a
registered pool database that does not resolve inside the workspace folder SHALL
be refused rather than opened.

#### Scenario: A traversal identifier is refused

- **WHEN** a client supplies a conversation, turn, or artifact identifier that contains a path separator or `..`
- **THEN** the request fails with an explicit error and no file outside the workspace folder is read, written, or deleted

#### Scenario: Two workspaces never share files

- **WHEN** two workspaces are registered for two different subjects and both the CLI and the pages are used against each
- **THEN** every path each operation touches lies inside its own workspace folder, and neither workspace's pool, figures, jobs, or plan file is reachable through the other's routes or commands

#### Scenario: A pool outside the workspace is refused

- **WHEN** a registered entry points its pool database outside the workspace folder
- **THEN** opening that workspace fails with an explicit error instead of reading the other folder's database

### Requirement: Workspace selection never guesses

When the registry holds several workspaces, a command that needs one SHALL NOT
fall back to the first registered entry. It SHALL fail with a message that names
the registered workspaces and shows a ready-to-paste command that selects one
explicitly.

#### Scenario: An ambiguous command is refused

- **WHEN** a workspace-scoped command runs without naming a workspace while two or more are registered
- **THEN** nothing is read or written, and the error names the registered workspaces with a paste-ready command that selects one

#### Scenario: A single registered workspace needs no name

- **WHEN** exactly one workspace is registered and a workspace-scoped command runs without a name
- **THEN** that workspace is used, as before

### Requirement: Chapter list derived from pool content

The workbench SHALL list the chapters of the active course by deriving them from
the content identifiers already in the pool (knowledge points, problems, cards).
It SHALL NOT introduce a chapters table, a chapter registry, or any chapter
registration step. A chapter SHALL appear as soon as content carrying its
identifier exists and SHALL disappear only when that content does.

#### Scenario: Chapters come from content

- **WHEN** the pool contains knowledge points or problems whose identifiers carry two different chapter segments
- **THEN** the chapter switch lists exactly those two chapters for the active course

#### Scenario: A new chapter appears without registration

- **WHEN** a batch of content for a chapter that has no content yet is applied to the pool
- **THEN** the new chapter appears in the switch without any additional command

#### Scenario: An empty pool offers no chapter

- **WHEN** the pool holds no content for the active course
- **THEN** the switch reports no chapters and the whole-course lens remains the only state

### Requirement: Chapter lens scoping

The chapter lens SHALL scope reading surfaces — knowledge-point list/detail,
knowledge graph, and practice suggestions — and MAY provide the default scope for
Paper Assembly. It SHALL NOT define or mutate the contents of a running Paper.
An explicitly chosen Paper-assembly scope MAY span chapters and SHALL survive
chapter-lens changes in the same tab until an explicit Agent/CLI authoring request changes that scope.

#### Scenario: Lens narrows default assembly suggestions

- **WHEN** one chapter is active and the learner has not established another explicit assembly scope
- **THEN** practice suggestions and default Paper Assembly use that chapter without creating an executable knowledge-point queue

#### Scenario: Explicit scope survives lens changes

- **WHEN** the learner has explicitly requested an Agent/CLI assembly scope spanning chapters and changes the reading lens
- **THEN** the selected assembly scope remains unchanged while the reading surfaces follow the new lens

Reading-lens and graph selection controls SHALL remain reading controls and SHALL NOT accumulate a learner-managed Paper Assembly scope.

### Requirement: Provenance-filtered problem pull

Problem pull SHALL accept `source_kind`, a derived mutually exclusive
`source_group`, and `origin_kinds` as a list of the ways a row may have been
produced (`source_problem`, `adapted_problem`, `generated_grounded`); a row is
kept when its `origin_kind` is **any** of the named ways. `ai_generated`
contains generated origin; `exam` contains non-generated
quiz/midterm/final/makeup sources; `textbook` contains non-generated textbook
sources; all remaining rows are `other`. Multiple filters intersect. Pull MAY
also filter by `exam_year`, matched as a prefix so that a value such as `2023`
selects every problem whose recorded year starts with it.

Pull SHALL additionally accept two keyword groups, `stem_keywords` and
`source_keywords`. Each group splits its input on whitespace, casefolds, and
keeps only rows carrying **every** one of its words in that domain's own text.
The two domains SHALL be defined once and read by every surface: the **stem**
domain is `display_title` + `problem_text`; the **source**
domain is `source_evidence` + `exam_year` + the leading run of `【…】` tags at
the head of `problem_text` (`^\s*((?:【[^】]*】)+)`), which is where pools
imported before the provenance fields existed still keep their source label.
When both groups carry words, the groups intersect. The single-value
`origin_kind` parameter SHALL NOT remain: a caller that cannot express more
than one way would be the only way this axis is used.

#### Scenario: AI exam-grounded problem stays in AI group

- **WHEN** a generated problem is grounded in final-exam material
- **THEN** the AI group includes it and the exam convenience group does not

#### Scenario: Combine source axes

- **WHEN** pull requests textbook material and adapted origin
- **THEN** only rows satisfying both values are returned

#### Scenario: More than one origin at a time

- **WHEN** pull names `source_problem` and `adapted_problem`
- **THEN** rows of both origins are returned and generated rows are not

#### Scenario: Select one exam year

- **WHEN** a pull carries an exam year
- **THEN** only problems whose recorded year starts with that value are returned

#### Scenario: Several stem words narrow together

- **WHEN** the stem group carries two words and only one problem carries both
- **THEN** that problem alone is returned

#### Scenario: A source label carried only in the 【…】 prefix

- **WHEN** a problem's `source_evidence` and `exam_year` are empty and its
  `problem_text` opens with `【2023期末】【合集A】`
- **THEN** a source keyword naming either tag selects it, and the tags are not
  read as source text anywhere but at the head of the text

### Requirement: Every learning action is reachable from the CLI

Every learning action the browser workbench can perform SHALL be reachable
through the super CLI in JSON form: recording a practice result, recording
feedback (including cards and directions), replacing a current state, and
managing goals. Where the HTTP API already validates an action or wraps it in
one transaction, the CLI SHALL apply the same validation and the same
transaction boundary, and a rejected action SHALL leave every row unchanged.
A CLI goal write SHALL invalidate the cached daily plan exactly as the API does.

#### Scenario: Recording a practice result is atomic

- **WHEN** the CLI records a practice result and one of the writes fails
- **THEN** no attempt, progress, or schedule row is left changed and the command exits nonzero

#### Scenario: An unknown problem is rejected before writing

- **WHEN** the CLI records a practice result for a problem id the pool does not hold
- **THEN** it exits nonzero naming the problem and nothing is written

#### Scenario: The Agent rates a card in a direction

- **WHEN** the Agent records feedback for a flash card with a direction through the CLI
- **THEN** only that schedule row advances and the signal, event, progress, and current-state semantics stay unchanged

#### Scenario: A CLI goal write invalidates the plan

- **WHEN** a goal is created, changed, or deleted through the CLI
- **THEN** the next daily-plan read rebuilds instead of serving the cached plan

### Requirement: Declared interface surface

One ownership table SHALL declare every HTTP API route and every CLI command
with its audience (Agent, human, both, or browser-only) and its status. A test
SHALL derive the real sets from the argument parser and the route table and
SHALL fail when a declared entry does not exist, when a real entry is
undeclared, or when an entry declared reachable from both surfaces lacks either
implementation. The human registration document SHALL point at this table as the
machine authority, and a surface that is deliberately browser-only SHALL be
declared as such rather than left unmentioned.

#### Scenario: An undeclared command fails the audit

- **WHEN** a command is added to the parser without being declared in the ownership table
- **THEN** the audit test fails and names the command

#### Scenario: A declared but missing entry fails the audit

- **WHEN** the table declares a command or route that does not exist in the code
- **THEN** the audit test fails and names the entry

#### Scenario: A both-surface entry needs both implementations

- **WHEN** an entry is declared reachable from the browser and from the Agent but only one side exists
- **THEN** the audit test fails until the missing side exists or the entry is re-declared

### Requirement: Durable attempt records for every surface

Every submitted answer SHALL become a durable, append-only attempt row regardless
of the surface that produced it — the browser practice flow, the CLI, or an
Agent manifest. A browser-submitted attempt SHALL store the answer text, the
chosen option texts when the item has options, and the objective verdict when
the item carries a usable answer key; a comprehensive answer SHALL store its
text with no verdict. An attempt row alone SHALL NOT move progress, schedule,
signals, or current state; those still move only through the rating flow, which
SHALL link its event back to the attempt (`attempt_id`) after validating that
the attempt belongs to the rated item. A pool that predates the columns SHALL
still accept the attempt (degraded, without verdict or choices) instead of
failing the practice flow.

#### Scenario: A browser answer is durable

- **WHEN** the student submits an answer on the practice page
- **THEN** one attempt row persists the answer text, the chosen options, and the objective verdict, and no learning projection changes until the rating lands

#### Scenario: The rating links back

- **WHEN** the session's rating is recorded for an item that submitted an attempt
- **THEN** the feedback event carries that attempt's id, and the attempt reads back with its rating

#### Scenario: A mismatched attempt id is refused

- **WHEN** a rating names an attempt that belongs to another item
- **THEN** the rating is refused with zero writes

### Requirement: Retry-safe browser practice writes

Browser answer submissions and ratings SHALL carry a stable `request_id`. Before
sending a write, the browser SHALL persist its exact payload and id with the
practice session and reuse them after a refresh or failed response. The server
SHALL store the request result atomically with its write: an exact retry SHALL
return the original result without another attempt, feedback event, or learning
projection update. Reusing an id for a changed operation or payload SHALL
return a conflict without writing. A rating SHALL retain the `attempt_id` link
to its answer.

#### Scenario: An answer response is lost

- **WHEN** the browser retries the saved answer request after a refresh
- **THEN** the original attempt id is returned and exactly one attempt exists

#### Scenario: A rating response is lost

- **WHEN** the browser retries the saved rating request after a refresh
- **THEN** its original result is returned and the linked rating applies once

#### Scenario: A request id is reused with changed content

- **WHEN** the browser sends a different answer or rating with an existing request id
- **THEN** the server returns a conflict and changes no learning row

### Requirement: Practice history is readable in the product

The workbench SHALL surface the practice history to the learner: a server-
rendered records view in the navigation listing recent attempts newest first —
problem link, verdict badge, rating, note, answer excerpt, time — filterable by
problem; and the practice reveal SHALL render the problem's past attempts (with
their linked ratings) from the already-served problem payload.

#### Scenario: The records view lists the history

- **WHEN** the learner opens the records view
- **THEN** recent attempts appear newest first with verdict and rating, and one problem's history can be isolated

#### Scenario: The reveal shows past attempts

- **WHEN** the student reveals a solution for a problem attempted before
- **THEN** the past attempts (bounded to the latest few) render with their verdicts and ratings

### Requirement: Multi-dimension source filters

Problem selection SHALL accept list-valued source dimensions alongside the
single-value ones: `source_kinds` (exact), `exam_years` (prefix),
`evidence_docs` (case-insensitive substring over the free-text source
evidence), and `origin_kinds` (any of the named production ways). Within one
dimension the values SHALL union; across dimensions they SHALL intersect. The
system SHALL derive each dimension's offered values from the pool's actual rows
with row counts, folding source evidence into one document key per source
document (an `.md`-style path verbatim, textbook rows into 教材, otherwise the
leading segment), and SHALL expose that census as a read-only endpoint plus
repeatable CLI flags (`--source-kind`, `--origin-kinds`, the new
`--source-evidence`). The pull API SHALL also accept `exam_year`, which it
previously ignored. The generic content search SHALL split its query on
whitespace and keep only rows carrying every one of its words.

#### Scenario: Dimensions union within and intersect across

- **WHEN** a selection names two source kinds of which one matches nothing, and an exam year
- **THEN** the rows matching the other kind and the year are returned, and rows matching the year but a different kind are not

#### Scenario: Evidence matching is fragment-friendly

- **WHEN** an evidence filter names a distinctive fragment of a document's name in any letter case
- **THEN** every row whose evidence contains that fragment is selected, whichever pool format wrote it

#### Scenario: Facets come from the pool

- **WHEN** the filter dimensions are requested
- **THEN** every offered value exists on at least one row, carries its row count, and one value per source document is offered

#### Scenario: Origin is a dimension like the others

- **WHEN** the filter dimensions are requested
- **THEN** the response carries a fourth dimension listing each production way
  present in the pool with its row count, in the same shape as the other three

#### Scenario: A content search with several words

- **WHEN** a content search is given two words and only one row carries both
- **THEN** that row alone is returned

### Requirement: Question corrections reset only affected unfinished items
Changing a question's stem/embedded answering content, options, answer key or answering type SHALL retain its identity and Paper memberships/order, reset only that question to pending in unfinished Paper executions, and discard only its stale answer/choice drafts. Other items' progress SHALL survive. Explanation/title/KP/difficulty/source-only changes and no-op edits SHALL NOT trigger reset. Historical attempts/ratings/runs SHALL remain historical and SHALL NOT be automatically regraded. A submit made against superseded Paper structure or answering content SHALL be rejected before any learning write, with a recoverable explanation.

#### Scenario: Correct a shared question's answer key
- **WHEN** question Q occurs in unfinished A/B and its answer key changes
- **THEN** only Q becomes pending in both, its old drafts are cleared, other items retain progress, and prior attempts/ratings remain unchanged

#### Scenario: Edit only explanation or metadata
- **WHEN** Q's explanation, title, knowledge-point labels, difficulty or source metadata changes without changing answering content
- **THEN** neither its completion marker nor its draft is reset and a current answer is not rejected solely for that metadata change

#### Scenario: Old page submits after correction
- **WHEN** an old page submits an answer after its question's answering content or Paper structure was superseded
- **THEN** it receives an explicit stale-content response and no attempt, feedback, signal or schedule effect is written

### Requirement: Question deletion preserves unrelated execution progress and history
Deleting a question SHALL clean its current memberships and unfinished item/draft references, but SHALL preserve every other item's state and every genuine historical attempt/rating/run. This SHALL be an explicit exception to full progress reset after a manual Paper membership edit. Cursors SHALL resolve to a surviving item; removing the last item SHALL NOT fabricate completion or learning evidence. Historical reads SHALL indicate deleted content without requiring an active question.

#### Scenario: Delete a question shared by multiple unfinished Papers
- **WHEN** Q is deleted from the pool while A/B both reference it
- **THEN** Q disappears from both current memberships/checkpoints, all other progress survives, and previous historical evidence stays readable as deleted content

### Requirement: Explicit final Paper submission

Only explicit `提交试卷` SHALL finish an ordinary-problem run. Final submission SHALL preserve explicit stuck marks, submit other existing nonblank input not already submitted, mark remaining blank items stuck, freeze final answers and archive one completed run. An explicit stuck mark SHALL take precedence over unchanged earlier input until a new answer edit clears the mark; retained draft text SHALL not be graded as the final answer of a stuck item. It SHALL NOT ask for an additional blank-item confirmation or wait for self-rating. Previously submitted items SHALL not create duplicate Attempts, feedback or learning effects. A whole-Paper editable draft or revisable stuck mark SHALL NOT become an immutable Attempt before final submission. Per-item explicit submissions and locked stuck marks SHALL use the existing submission/evidence flow; navigation and draft saving SHALL never create evidence.

Submission SHALL be retry-safe and validate execution, Paper generation and item content revisions. A failed submission SHALL retain recoverable input and show failure rather than show completion. A lost response SHALL be resolvable without resubmitting evidence or archiving again. Existing immutable historical Attempts SHALL NOT be rewritten to emulate editable drafts.

#### Scenario: Submit filled and blank items
- **WHEN** a run is finally submitted with saved inputs, some unsubmitted multiple-choice/text answers and some blank items
- **THEN** filled inputs are submitted as answers, only blank items become stuck, and the run completes without a second confirmation or mandatory rating

#### Scenario: Last per-item result is not final submission
- **WHEN** the last pending item receives a per-item answer or stuck submission
- **THEN** the learner may still browse the run and only explicit final submission archives it

#### Scenario: Explicit stuck mark overrides unchanged draft
- **WHEN** a learner enters an answer, marks it stuck in whole-Paper mode, and submits without a new answer edit
- **THEN** the final item remains stuck without grading the unchanged draft as a submitted answer
- **AND** a new nonblank answer edit before final submission may clear the mark without erasing the reference-view fact

#### Scenario: Retry after a lost final response
- **WHEN** the same final submission is retried after its response is lost
- **THEN** the original completed result is recovered without duplicate Attempts, feedback, learning effects or run snapshots

#### Scenario: Failed or stale submission
- **WHEN** final submission fails or a referenced revision is stale
- **THEN** no successful completion is claimed and saved input remains recoverable under the existing revision/reset rules
