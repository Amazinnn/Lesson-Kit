## ADDED Requirements

### Requirement: Agent CLI calls preserve error feedback

The Agent prompt SHALL give the correct workspace-aware CLI argument order and
direct the Agent to query the relevant subcommand help when uncertain. Lesson
Kit invocations SHALL be issued independently without output pipelines,
failure-suppressing fallbacks, or trailing commands masking their exit status.
The Bridge SHALL use provider-reported activity outcomes rather than classify
failure by matching words in output. A failed tool call MAY be followed by a
corrected invocation without automatically failing the whole conversation.

#### Scenario: Invalid CLI arguments

- **WHEN** an independent CLI invocation omits a required workspace or supplies unknown arguments
- **THEN** it returns nonzero with diagnostic output and a provider-reported error is retained as a failed activity

#### Scenario: Successful output mentions error

- **WHEN** a provider reports success and its output contains the word error
- **THEN** the Bridge does not override success based on that text

#### Scenario: Corrected invocation succeeds

- **WHEN** the Agent corrects a failed invocation and issues a new successful call
- **THEN** both activities retain their own outcomes and the Agent reports success only from the successful result
