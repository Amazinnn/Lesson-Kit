## REMOVED Requirements

### Requirement: Task lifecycle

**Reason:** the explain/diagnose task machinery is removed entirely (owner
decision 2026-08-29); no remaining capability uses job tasks.

### Requirement: Output-contract validation

**Reason:** contract validation existed only for explain/diagnose task results.

### Requirement: Explain operation

**Reason:** removed by owner decision — per-problem explanation is unnecessary
specialization when the agent's context is the whole page.

### Requirement: Teacher conduct contract

**Reason:** conduct rules were carried in task instruction text for the removed
operations; conversations carry their own conduct in the teaching layer.

### Requirement: Diagnose operation

**Reason:** removed together with explain (same owner decision).

### Requirement: Bridge artifact locations

**Reason:** job working files and explain results no longer exist; conversation
mirrors keep their locations per the conversation-mirror requirement.

### Requirement: Practice-page one-click tasks

**Reason:** the practice-page explain/diagnose entries are removed with the
operations they invoked.

## MODIFIED Requirements

### Requirement: Provider configuration

The bridge SHALL read provider definitions (command, arguments, working
directory mode, timeout) from a config file, and the workbench SHALL expose
provider configuration as a CLI operation. Configured values serve as
conversation-provider overrides (arguments, model, timeout) for the locally
discovered agent CLIs.

#### Scenario: Configure a provider

- **WHEN** the user runs `wb bridge add <provider> --command <cmd>`
- **THEN** the provider is written to the bridge config and applies to
  conversations that use that provider

### Requirement: CLI is a data interface, not a teacher

The super CLI SHALL expose only data operations — query pool content, pull
problems, record attempts and feedback, read workspace state — and SHALL carry
no teaching semantics. Teaching behavior (how to teach, when to ask, how to
close a topic) SHALL live in the teaching layer (skills and teaching
contracts), never in the CLI. The same teaching capability SHALL be reachable
through the web shell, whose AI panel is a thin conversation surface over the
same bridge conversations.

#### Scenario: CLI records data without pedagogy

- **WHEN** an agent runs `wb pull` and `wb record` to gather and record practice data
- **THEN** the CLI returns and stores data only, with no teaching instructions, and the agent's teaching behavior comes from the teaching skill it loaded

### Requirement: Workbench operates without AI

The workbench SHALL be fully functional with no provider configured and no AI
conversation ever started: registry, weak list, pull, practice, feedback, and
scheduling SHALL work identically with or without the bridge.

#### Scenario: Practice without any provider

- **WHEN** no bridge provider is configured and the learner practices problems
- **THEN** every non-AI feature works unchanged and AI conversations are shown as unavailable rather than broken
