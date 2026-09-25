## MODIFIED Requirements

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted it SHALL report the shortage per knowledge
point instead of inventing content; no candidate staging exists to fall back on.
A pull MAY additionally accept explicitly named problem ids, which SHALL be
included even when they fall outside the requested knowledge points or the
active filters, and MAY select by learner evidence — weak knowledge points, due
problems, and previously wrong problems. Every returned problem SHALL carry the
reason it was selected. The weakness order used by learner-driven selection is
the weak-point score; the `weak` ordering mode of a session pull orders by
how many requested knowledge points a problem covers and is unchanged.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered, with none repeated within the same session

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point and the UI points to the Check pipeline as the content path instead of fabricating problems

#### Scenario: Explicitly named problems always come back

- **WHEN** a pull names a problem id outside the requested knowledge points
- **THEN** that problem is returned with its selection reason while the scope still governs the rest

#### Scenario: Learner evidence selects problems

- **WHEN** a pull selects by weak knowledge points, by due problems, or by previously wrong problems
- **THEN** the returned problems are exactly those its evidence marks, and each carries the matching reason

### Requirement: Scoped include filter

A scoped pull MAY carry `include_ids`; returned problems SHALL then be
restricted to those identifiers within the requested knowledge-point scope.
Combining `include_ids` with the unscoped `all` mode SHALL be rejected, and
the shortage report SHALL keep reflecting the remaining unfilled demand. The
super CLI SHALL expose the same filter, so a caller that can reach `/pull` is
not limited to the browser for it.

#### Scenario: Pull one due problem

- **WHEN** a scoped pull carries `include_ids` with one durable problem id
- **THEN** only that problem is returned

#### Scenario: Include filter with unscoped all mode

- **WHEN** a pull carries `include_ids` together with `mode: all`
- **THEN** the request is rejected with 400 and nothing is pulled

#### Scenario: Agent uses the include filter

- **WHEN** the Agent passes the include filter to the CLI
- **THEN** the same restriction applies and the response reports the same shortage

### Requirement: Provenance-filtered problem pull

Problem pull SHALL accept `source_kind`, `origin_kind`, and a derived mutually
exclusive `source_group`. `ai_generated` contains generated origin; `exam`
contains non-generated quiz/midterm/final/makeup sources; `textbook` contains
non-generated textbook sources; all remaining rows are `other`. Multiple
filters intersect. Pull MAY also filter by `exam_year`, matched as a prefix so
that a value such as `2023` selects every problem whose recorded year starts
with it.

#### Scenario: AI exam-grounded problem stays in AI group

- **WHEN** a generated problem is grounded in final-exam material
- **THEN** the AI group includes it and the exam convenience group does not

#### Scenario: Combine source axes

- **WHEN** pull requests textbook material and adapted origin
- **THEN** only rows satisfying both values are returned

#### Scenario: Select one exam year

- **WHEN** a pull carries an exam year
- **THEN** only problems whose recorded year starts with that value are returned

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

## ADDED Requirements

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
