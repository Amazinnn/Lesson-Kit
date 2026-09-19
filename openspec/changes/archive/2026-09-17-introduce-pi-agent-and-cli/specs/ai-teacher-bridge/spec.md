## MODIFIED Requirements

### Requirement: Provider-native conversation discovery

The bridge SHALL discover supported Agent CLIs from PATH. Codex, Claude, and Pi
SHALL be offered when their executables exist, with optional registry
configuration limited to command, arguments, model, and timeout. When the
registry configures an explicit command for a provider, that executable SHALL
take precedence over PATH discovery, so the resolved executable is never left
to PATH ordering alone. A conversation SHALL lock its selected provider. The
bridge SHALL NOT silently switch provider, create a replacement provider
session, or hide authentication, timeout, cancellation, nonzero-exit, or
provider-session-loss errors. A provider that reports a failure inside its own
event stream while still exiting zero SHALL be surfaced as a failed turn with
the provider's stated reason.

#### Scenario: Discover a local provider

- **WHEN** `codex`, `claude`, or `pi` is present on PATH
- **THEN** the providers endpoint lists it without requiring a duplicate command registration

#### Scenario: Explicit executable takes precedence over PATH

- **WHEN** the registry configures an explicit command for a provider whose name is also present on PATH
- **THEN** the provider is launched from the configured executable, and the providers listing reports that resolved path

#### Scenario: Provider fails during a turn

- **WHEN** the selected provider exits, times out, is cancelled, or cannot resume its native session
- **THEN** that turn reports the actual failure and the conversation remains locked to the same provider

#### Scenario: Provider reports failure inside its stream while exiting zero

- **WHEN** the provider process exits successfully but its event stream carries an error result
- **THEN** the turn is reported as failed with the provider's stated reason instead of as an answer-less success

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
- **THEN** the provider still receives the fixed workspace/page context and can use `wb data` to search the pool

#### Scenario: Pi session id is taken from the provider's own header

- **WHEN** a Pi conversation completes its first turn
- **THEN** the native session id recorded for later resumption is the one the provider announced in its session header, not a server-generated identifier
