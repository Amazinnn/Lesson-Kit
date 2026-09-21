## MODIFIED Requirements

### Requirement: Provider configuration

The bridge SHALL read provider definitions (command, arguments, working
directory mode, timeout) from a config file, and the workbench SHALL expose
provider configuration as a CLI operation. Configured values serve as
conversation-provider overrides (arguments, model, timeout) for the locally
discovered agent CLIs.

#### Scenario: Configure a provider

- **WHEN** the user runs `lesson-kit bridge add <provider> --command <cmd>`
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

- **WHEN** an agent runs `lesson-kit pull` and `lesson-kit record` to gather and record practice data
- **THEN** the CLI returns and stores data only, with no teaching instructions, and the agent's teaching behavior comes from the teaching skill it loaded

### Requirement: Native session continuity

Codex conversations SHALL use stable exec/resume JSONL commands, Claude
conversations SHALL use print/resume stream-json commands, and Pi conversations
SHALL use print mode with JSON output plus native session resumption. The
provider SHALL run in the registered workspace, inherit local authentication,
configuration, skills, session store, and project instructions, and receive an
appended Lesson Kit teacher contract and server-rebuilt page context.

#### Scenario: Continue an existing provider session

- **WHEN** a learner sends a second turn in a conversation whose provider session id is known
- **THEN** the bridge invokes that provider's native resume command with the same session id

#### Scenario: Send a context-free learning question

- **WHEN** the learner asks a question while no practice problem is active
- **THEN** the provider still receives the fixed workspace/page context and can use `lesson-kit data` to search the pool

#### Scenario: Pi session id is taken from the provider's own header

- **WHEN** a Pi conversation completes its first turn
- **THEN** the native session id recorded for later resumption is the one the provider announced in its session header, not a server-generated identifier
