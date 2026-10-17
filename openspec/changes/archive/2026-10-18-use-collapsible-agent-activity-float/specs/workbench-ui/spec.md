## MODIFIED Requirements

### Requirement: Agent runtime work uses transient auxiliary surfaces

Short and sustained provider activity SHALL use only the top-right replaceable
Activity Float for progress and current milestones. A Bottom Dock SHALL NOT
open or reserve middle-page height during work. The Float SHALL remain bounded
and SHALL NOT become a history dashboard or raw event wall. Existing
conversation activity/history SHALL remain authoritative.

#### Scenario: A short activity is visible

- **WHEN** a provider reports a short activity
- **THEN** the Activity Float shows its readable label and current state, and a
  later short activity replaces that float content

#### Scenario: Work continues across milestones

- **WHEN** a provider reports sustained multi-step work
- **THEN** the same top-right Activity Float summarizes current milestones and
  latest status while the middle page keeps its height and no Bottom Dock opens

#### Scenario: Detailed output is available

- **WHEN** an activity includes provider output
- **THEN** the transient surface keeps the semantic summary visible and the
  detailed output remains behind the existing closed disclosure in the
  conversation

#### Scenario: A provider confirms a failure

- **WHEN** the provider reports that the current turn failed
- **THEN** the work surface shows a concise failure summary and retains detailed
  output behind the existing closed disclosure

#### Scenario: Progress cannot be read

- **WHEN** a progress request fails while the provider turn has no authoritative
  terminal status
- **THEN** the interface reports that progress is unavailable, keeps the
  current turn gated against another send, and does not label the provider turn
  as failed

### Requirement: Explicit collapse applies to the current Agent turn

A small keyboard-accessible control SHALL expand or collapse the Activity
Float with a truthful label and `aria-expanded`. Collapsing SHALL leave a
compact reopening control while runtime progress is available. Later activity
updates in the same user turn SHALL NOT automatically reopen the Float;
explicit expansion MAY reopen it. A new user turn SHALL reset this suppression.
Switching conversations SHALL clear the prior conversation's transient
surfaces and collapse state. Idle SHALL NOT leave an empty Float or placeholder
panel.

#### Scenario: Collapse while work is running

- **WHEN** the learner collapses the Activity Float during a user turn and
  another activity arrives
- **THEN** the new activity remains in the conversation history, the Float
  stays closed and the small reopening control remains available

#### Scenario: Start a later user turn

- **WHEN** the learner sends a new message after the previous turn has ended
- **THEN** automatic Activity Float presentation is enabled for the new turn

#### Scenario: Switch conversations

- **WHEN** the learner opens a different conversation
- **THEN** no activity surface or collapse state from the previous conversation
  appears in the new one

#### Scenario: Reopen the current Float explicitly

- **WHEN** the learner activates the collapsed Float's small control
- **THEN** current progress reopens without changing the selected middle page or
  starting another task

#### Scenario: No runtime activity remains

- **WHEN** the current Agent turn has ended and no activity remains
- **THEN** the Activity Float and its reopening control are removed
