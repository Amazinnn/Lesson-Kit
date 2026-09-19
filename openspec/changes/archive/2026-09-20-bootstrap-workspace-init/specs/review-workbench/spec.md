## MODIFIED Requirements

### Requirement: Unified CLI entry point

The workbench SHALL expose its super CLI under both the `wb` and `lesson-kit`
command names, backed by the same implementation and the same subcommands. The
CLI serves two audiences over one implementation: a small, stable human surface
(init, use, dashboard, daemon, ls, bridge, doctor) and an agent surface (data,
pull, practice, feedback, ingest, goals). `lesson-kit init <path>` SHALL
register a workspace exactly as `wb init` does; when the folder is not yet a
lesson-kit workspace, it SHALL instead create one — pool database,
`.lessonkit/` skeleton — from the given course, without modifying existing
data. `lesson-kit dashboard` SHALL ensure the local workbench service is
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

## ADDED Requirements

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
