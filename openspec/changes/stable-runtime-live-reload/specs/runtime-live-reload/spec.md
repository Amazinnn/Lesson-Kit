## ADDED Requirements

### Requirement: Explicit and stable runtime source
Dashboard, daemon start and serve SHALL default to the primary Git checkout of the installed source, independent of course cwd or linked worktree cwd. Explicit `--project-root PATH` SHALL override the runtime source without changing course resolution or reinstalling the package. Children SHALL actually import that source. Daemon status, dashboard and doctor SHALL report verified source, PID, port and reload state. Service reuse SHALL require matching identity, not PID liveness alone. Unknown legacy identity or source mismatch SHALL be diagnosed without killing an unrelated or busy service.

#### Scenario: Editable install in a worktree
- **WHEN** the installed package resides in a linked worktree and dashboard runs in a course folder
- **THEN** the service imports the primary checkout and reports its path

#### Scenario: Explicit preview
- **WHEN** a source path and isolated port are specified
- **THEN** the preview imports and watches that path without changing the default source

### Requirement: Safe automatic runtime updates
Python implementation edits and rollback SHALL reload the application after debounce; served asset edits SHALL refresh browser presentation. Source invalidity SHALL leave the last usable worker running with an error notice. Changes SHALL be detected by file metadata without new dependencies or content hashes. Pools, jobs, caches, tests and Git metadata SHALL not trigger reload. Build-only frontend source changes SHALL require the documented build/watch command.

#### Scenario: Agent busy
- **WHEN** source changes while an Agent turn, queued follow-up or approval/action operation remains active
- **THEN** the user sees an update-pending notice and no task is aborted
- **AND** the update applies only after admission is closed atomically with a quiescent check, all in-flight request writes complete, and the queue remains safe

#### Scenario: Broken edit then correction
- **WHEN** changed Python has invalid syntax
- **THEN** the running usable process remains available with an actionable update error
- **AND** a later valid edit can be applied without a crash loop

### Requirement: Browser refresh retains user input
Automatic page refresh SHALL preserve unsent Agent text, pending message edits, unsubmitted answer drafts, goals and experience edits, with selection where available. It SHALL not send messages or submit answers. A visible pending notice SHALL explain any refresh deferral necessary to preserve input.

#### Scenario: Refresh with unsent content
- **WHEN** assets or the worker generation changes while a learner has unsent text
- **THEN** refresh restores the text in its original surface without triggering submission or learning evidence
