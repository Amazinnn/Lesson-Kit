## ADDED Requirements

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
