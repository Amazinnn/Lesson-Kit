## ADDED Requirements

### Requirement: Runtime source selection

`lesson-kit dashboard`, `lesson-kit daemon start` and `lesson-kit serve` SHALL
serve, watch and report the checkout that contains the installed `lesson-kit`
code — the checkout whose `workbench` package the running CLI imports —
independent of the course working directory and independent of whether that
checkout is a linked Git worktree. An explicit `--project-root PATH` SHALL
serve and watch that path for that run without changing the default source, the
course resolution or the installation. A path that is not a lesson-kit source
directory SHALL be rejected with its reason and SHALL NOT start a service. The
source reported by `daemon status`, `doctor` and `/api/runtime` SHALL be the
source actually served.

#### Scenario: Editable install in a linked worktree

- **WHEN** the installed package resides in a linked worktree and the user runs
  `lesson-kit daemon start` from a course folder
- **THEN** the service imports, watches and reports that worktree
- **AND** the primary checkout is neither served nor reported

#### Scenario: Explicit preview of another checkout

- **WHEN** the user passes `--project-root PATH` with an isolated port
- **THEN** that path is served and watched for the run
- **AND** the default source stays unchanged

#### Scenario: Reject a path that is not a lesson-kit source

- **WHEN** `--project-root` names a directory that does not contain the
  lesson-kit source
- **THEN** the command fails with that reason and no service is started
