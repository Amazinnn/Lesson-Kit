## ADDED Requirements

### Requirement: Pi activities are conversation messages

The chat SHALL render each Pi concrete activity as an independent compact
message in event order. Updates with the same activity id SHALL update that
message in place. Tool output SHALL be collapsed by default. Codex and Claude
SHALL continue using the existing execution-plan presentation.

#### Scenario: Pi command completes

- **WHEN** a Pi command activity changes from running to done
- **THEN** one compact message changes state without adding a duplicate row

#### Scenario: Output is present

- **WHEN** a Pi activity carries command or tool output
- **THEN** the output is available behind a closed disclosure for running, done, and failed states

### Requirement: Pi text follows event chronology

Contiguous Pi text deltas SHALL grow one assistant bubble. A concrete activity
after text SHALL close that segment; later text SHALL start a new bubble after
the activity. The durable successful mirror may restore the coalesced activities
before the final combined answer.

#### Scenario: Tool call interrupts text

- **WHEN** Pi emits text, then a tool activity, then more text
- **THEN** the chat shows text bubble, activity message, and a new text bubble in that order

