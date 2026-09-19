## ADDED Requirements

### Requirement: Unified CLI entry point

The workbench SHALL expose its super CLI under both the `wb` and `lesson-kit`
command names, backed by the same implementation and the same subcommands.
`lesson-kit init <path>` SHALL register a workspace exactly as `wb init` does.
`lesson-kit dashboard` SHALL ensure the local workbench service is running and
open the workbench in the browser; it SHALL NOT introduce a fourth workbench
page or reinterpret the existing three-page shell.

#### Scenario: Register a workspace through the lesson-kit command

- **WHEN** the user runs `lesson-kit init <path> --course <course> --chapter <chapter>`
- **THEN** the folder is registered with that course and chapter and appears in the hub, identically to `wb init`

#### Scenario: Open the dashboard

- **WHEN** the user runs `lesson-kit dashboard` while no service is running
- **THEN** the service is started in the background, the workbench URL is opened in the browser, and the command reports success only after the service actually answers

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
