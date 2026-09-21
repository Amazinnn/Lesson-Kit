## Purpose

The review workbench is the consumption side of lesson-kit: a browser workbench
and shared CLI that turn the SQLite pool into weak-point-first daily practice,
with flexible feedback and a forgetting curve used as background guidance only.
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

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted it SHALL report the shortage per knowledge
point instead of inventing content; no candidate staging exists to fall back on.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered, with none repeated within the same session

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point and the UI points to the Check pipeline as the content path instead of fabricating problems

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
interval, due date) updated on practice results. Scheduling SHALL influence
ordering and on-demand suggestions only; it SHALL never hide, lock, or refuse
items, and due items SHALL NOT be surfaced as a standing due list or through a
separate review page. Due knowledge points SHALL be reachable as on-demand
suggestions inside the practice page's staged-list flow, each with at most one
human-readable reason phrase.

#### Scenario: Due items are reminded

- **WHEN** the workspace home is opened with due schedule rows whose knowledge
  points are not currently selected
- **THEN** the practice page's suggestion entry shows their count, and
  expanding it lists each due knowledge point with one human reason phrase,
  never raw scheduler parameters

#### Scenario: Schedule state updates after practice

- **WHEN** a problem result is recorded
- **THEN** its repetitions, ease, interval, and due date are updated in the
  scheduling table

### Requirement: Session interruption recovery

Recorded learning conclusions SHALL remain durable in the pool. The active practice mode, current problem, seen-problem set, and unified-rating queue SHALL remain tab-scoped in the existing browser session storage and SHALL be restored after refresh or page navigation in the same tab. Closing the tab MAY end unsubmitted active-session state and SHALL NOT manufacture a durable learning record.

#### Scenario: Resume after refreshing practice

- **WHEN** the learner refreshes or leaves and returns to practice in the same tab
- **THEN** the selected mode, current problem, seen-problem set, and pending unified ratings are restored without pulling a duplicate problem

#### Scenario: Recorded results survive browser closure

- **WHEN** the learner closes the browser after submitting ratings and later reopens the workspace
- **THEN** those recorded results remain in the pool and are reflected in later ordering

#### Scenario: Resume after closing the browser

- **WHEN** the learner closes the browser mid-session and later reopens the workspace
- **THEN** recorded results are intact and practice can begin from current pool state without inventing records for the closed tab's unfinished actions

#### Scenario: Unsubmitted state creates no record

- **WHEN** the browser tab ends with a draft, skipped item, or pending unsubmitted rating
- **THEN** no attempt, feedback, signal, progress, or schedule row is added for that unfinished action

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

The live graph model SHALL expose each knowledge point's formal-problem count and existing importance classification, and each semantic edge's explicit strength, shared-formal-problem count, and computed attraction. Edges SHALL originate only from formal knowledge relations or existing `related_kp_ids`. Reverse duplicate edges SHALL be merged, and shared problems SHALL reinforce but SHALL NOT create semantic edges.

#### Scenario: Count formal problems per node

- **WHEN** formal and candidate problems refer to a knowledge point with an existing importance value
- **THEN** `problem_count` includes only formal problems and the graph node reports that importance value

#### Scenario: Merge a bidirectional semantic edge

- **WHEN** two knowledge points relate to each other through duplicate or reverse relation declarations
- **THEN** the graph model returns one edge for that unordered pair

#### Scenario: Reinforce an existing relation with shared problems

- **WHEN** two related knowledge points share formal problems
- **THEN** their edge reports the shared count and higher computed attraction

#### Scenario: Do not infer a relation from co-occurrence

- **WHEN** two knowledge points share a problem but have no formal relation or `related_kp_ids` link
- **THEN** the graph model returns no edge between them

### Requirement: Unified Agent data CLI

The workbench SHALL expose JSON data commands for get, list, search, history,
create, update, delete, current-state replacement, candidate gating, and
candidate promotion across knowledge points, formal problems, candidate
problems, and knowledge relations. Read operations SHALL perform zero writes.
Within this data CLI a formal problem SHALL be created only by promoting a
candidate that has passed both existing gates. The candidate command family
SHALL be retired (待退役): it receives no new capabilities, and the Check
pipeline SHALL be the content path for adding formal problems.

#### Scenario: Search without a write

- **WHEN** an Agent searches the pool through `lesson-kit data`
- **THEN** matching structured entities are returned and no content, learning, sequence, or conversation row changes

#### Scenario: Edit a candidate

- **WHEN** candidate content is explicitly updated
- **THEN** the candidate is updated and both gate states reset to pending

#### Scenario: Promote a gated candidate

- **WHEN** a candidate has passed structure and audit gates and the Agent explicitly promotes it
- **THEN** one formal problem with a readable sequence id is created and the candidate reflects promotion

### Requirement: Readable content sequences

New knowledge points, formal problems, candidates, and relations SHALL receive course/chapter-scoped sequential readable identifiers allocated atomically from an additive sequence table. Existing numeric identifiers SHALL seed the next value. No hash-derived identifier SHALL be used.

#### Scenario: Allocate after existing content

- **WHEN** the chapter already contains numbered entities and a new entity is explicitly created
- **THEN** its id uses the next readable number in that entity scope without scanning to reuse a deleted id

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

### Requirement: Scoped include filter

A scoped pull MAY carry `include_ids`; returned problems SHALL then be
restricted to those identifiers within the requested knowledge-point scope.
Combining `include_ids` with the unscoped `all` mode SHALL be rejected, and
the shortage report SHALL keep reflecting the remaining unfilled demand.

#### Scenario: Pull one due problem

- **WHEN** a scoped pull carries `include_ids` with one durable problem id
- **THEN** only that problem is returned

#### Scenario: Include filter with unscoped all mode

- **WHEN** a pull carries `include_ids` together with `mode: all`
- **THEN** the request is rejected with 400 and nothing is pulled

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
command instead of a bare argument error. `lesson-kit init [path]` SHALL
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

`lesson-kit use <course> <chapter>` SHALL switch the active course and chapter
of the current workspace in the registry. When several workspaces are
registered, the workspace SHALL be selectable explicitly. A switch SHALL NOT
create, move, or delete any data, and an unknown workspace or missing argument
SHALL be reported as an error without changing stored state.

#### Scenario: Switch the active chapter

- **WHEN** the user runs `lesson-kit use <new-course> <new-chapter>`
- **THEN** subsequent hub, page, and prefix queries resolve against the new course and chapter, and no pool file was modified

#### Scenario: Switching never happens silently on error

- **WHEN** the user names a workspace that is not registered or omits an argument
- **THEN** the command fails with a clear message and the registry is unchanged

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

