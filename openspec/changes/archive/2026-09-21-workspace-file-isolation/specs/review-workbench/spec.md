## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Workspace registry

Each lesson-kit folder is a workspace. The registry maps a workspace name to a
folder path, its pool database, and its active course/chapter. A workspace can
be registered, listed, and opened (web shell or CLI), and a registered
workspace SHALL appear in the hub with its pool statistics.

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
- **THEN** it shows each registered workspace with course, chapter, knowledge-point count, problem count, due-item count, and weak-signal count

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
