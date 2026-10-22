## ADDED Requirements

### Requirement: Complete CLI discovery and entry-point parity

The workbench SHALL expose every supported command in its actual argparse help
tree, including `evidence`, `experience`, `mirror`, `papers` and the nested
`ingest <workspace> bundle` command. The installed `lesson-kit` command,
`python -m workbench.cli.main` and `python -m workbench.cli.entry` SHALL use the
same argument definitions and dispatch behavior. Command inventory SHALL derive
from that real parser. Existing argument semantics, validation, JSON receipts
and exit statuses SHALL remain compatible.

#### Scenario: Discover an existing extension command

- **WHEN** an operator requests root help using any public entry point
- **THEN** all supported top-level commands, including the four extensions, appear
- **AND** requesting extension or nested bundle help succeeds without workspace writes

#### Scenario: Save and read a managed paper through either entry point

- **WHEN** an Agent saves a valid paper manifest in an isolated workspace
- **THEN** each public entry point accepts the same arguments and returns the existing JSON receipt
- **AND** list and get return the same saved paper without re-ingesting its questions

#### Scenario: Invalid extension arguments

- **WHEN** an operator supplies invalid arguments to an extension command
- **THEN** all public entry points preserve argparse validation and a nonzero exit status
