## MODIFIED Requirements

### Requirement: Unified CLI entry point

The workbench SHALL expose its super CLI under both the `wb` and `lesson-kit`
command names, backed by the same implementation and the same subcommands. The
CLI serves two audiences over one implementation: a small, stable human surface
(init, use, dashboard, daemon, ls, bridge, doctor) and an agent surface (data,
pull, practice, feedback, ingest, goals). The human surface SHALL stay
parameter-light: beyond the subcommand name, a human command SHALL require at
most two parameters, SHALL default or derive every value it can infer, and when
it cannot infer a required value it SHALL fail with a ready-to-paste complete
command instead of a bare argument error. `lesson-kit init [path]` SHALL
register a workspace exactly as `wb init` does, with the path defaulting to the
current directory; when the folder is not yet a lesson-kit workspace, it SHALL
instead create one — pool database, `.lessonkit/` skeleton — without modifying
existing data. Its course SHALL come from an explicit `--course`, else from the
pool database name of an already-initialized workspace, else from the folder
name when that name is ASCII-safe (lowercased, runs of non-alphanumeric
characters folded to `-`); a folder name that cannot yield a lowercase ASCII
slug SHALL be reported with a ready-to-paste command rather than guessed.
`lesson-kit dashboard` SHALL ensure the local workbench service is
running and open the workbench in the browser; it SHALL NOT introduce a fourth
workbench page or reinterpret the existing three-page shell.

#### Scenario: Register a workspace through the lesson-kit command

- **WHEN** the user runs `lesson-kit init <path> --course <course> --chapter <chapter>`
- **THEN** the folder is registered with that course and chapter and appears in the hub, identically to `wb init`

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

- **WHEN** the user runs `lesson-kit init` inside a folder whose name is not ASCII
- **THEN** nothing is created, and the error prints a ready-to-paste `lesson-kit init --course <slug>` command naming that folder

#### Scenario: Already-initialized folder needs no course

- **WHEN** the user runs `lesson-kit init` inside a folder that already contains a pool database and is not registered
- **THEN** the course is taken from that database's name and the folder is registered without a `--course` flag

## ADDED Requirements

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
