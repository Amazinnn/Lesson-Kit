## ADDED Requirements

### Requirement: Provider turn budgets follow progress

A provider turn budget SHALL measure silence rather than total duration: every
provider record or output line SHALL reset it, and while a command or tool call
is in flight the longer tool budget SHALL apply, so a slow command is never cut
off mid-run. A turn that produces no record for the applicable budget SHALL fail
as a provider timeout through the existing failure path. The tool budget SHALL be
at least the silence budget and remain shorter than the idle process window, so a
stuck turn fails with its own reason before its provider process is recycled.
Both budgets SHALL be configurable per provider, and the default silence budget
SHALL NOT be shorter than the one already in force.

#### Scenario: A long answer is not a timeout

- **WHEN** a provider keeps reporting events for longer than the silence budget
- **THEN** the turn keeps running and is never failed as a timeout for taking a long time

#### Scenario: A slow command is not cut off

- **WHEN** a command or tool call runs without output for longer than the silence budget
- **THEN** the turn keeps running for at least the tool budget and the command is allowed to finish

#### Scenario: Real silence is still a stall

- **WHEN** nothing arrives for the silence budget while no command is in flight
- **THEN** the turn fails as a provider timeout, the process is stopped, and no transcript entry is written

#### Scenario: The budgets are visible and configurable

- **WHEN** a provider is configured or listed
- **THEN** both its silence budget and its tool budget are readable, and the tool budget is below the process idle window
