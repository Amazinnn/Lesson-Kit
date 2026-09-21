## MODIFIED Requirements

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

### Requirement: Course and chapter switching

`lesson-kit use <course> <chapter>` SHALL switch the active course and chapter
of the current workspace in the registry. When several workspaces are
registered, the workspace SHALL be selectable explicitly. A switch SHALL NOT
create, move, or delete any data, and an unknown workspace or missing argument
SHALL be reported as an error without changing stored state. A course value that
is not a lowercase ASCII slug SHALL be rejected with the reason, since it
prefixes every content id.

#### Scenario: Switch the active chapter

- **WHEN** the user runs `lesson-kit use <new-course> <new-chapter>`
- **THEN** subsequent hub, page, and prefix queries resolve against the new course and chapter, and no pool file was modified

#### Scenario: Switching never happens silently on error

- **WHEN** the user names a workspace that is not registered or omits an argument
- **THEN** the command fails with a clear message and the registry is unchanged
