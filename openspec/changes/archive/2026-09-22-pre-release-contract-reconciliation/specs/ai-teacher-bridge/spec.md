## ADDED Requirements

### Requirement: Conversation mirror consistency during polling

The bridge SHALL keep conversation metadata, turn metadata, event streams, and
successful transcripts readable while an active provider turn updates them.
In-process readers and writers SHALL observe complete JSON values and complete
JSONL records; a polling read SHALL NOT cause a provider turn to fail because
the mirror file is being replaced.

#### Scenario: Poll while conversation metadata changes

- **WHEN** the browser polls a turn while the worker updates the conversation mirror
- **THEN** the poll reads either the prior or next complete value and the worker continues without a sharing violation

#### Scenario: Poll while an event is appended

- **WHEN** one thread appends the next sequenced event while another reads events
- **THEN** the reader receives only complete records with strictly increasing sequence numbers
