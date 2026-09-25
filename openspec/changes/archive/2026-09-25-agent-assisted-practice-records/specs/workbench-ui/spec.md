## MODIFIED Requirements

### Requirement: Authoritative page context for Agent turns

For each turn, the browser SHALL send object identifiers rather than the full
page DOM; the server SHALL rebuild authoritative workspace, course, chapter,
route, page type, selected object, and relevant learning context from SQLite.
Practice, knowledge-point, and graph pages SHALL retain their existing
object/state summaries and the latest three distinct browser-session anchors.
On the practice page, the current unsent answer text, selected options, note,
and currently displayed image references SHALL also be passed as bounded,
ephemeral learner input. They SHALL be treated as draft content, not database
facts, and SHALL NOT be written to the pool or conversation mirror merely by
sending a turn. Other pages keep their existing context behavior.

#### Scenario: Ask about a knowledge point page

- **WHEN** the learner sends a turn from a knowledge-point page
- **THEN** the Agent receives current content, evidence, schedule, neighbours, and related problems rebuilt from the workspace

#### Scenario: Keep a practice draft private

- **WHEN** an unsubmitted answer or note exists but no Agent turn or explicit practice submission occurs
- **THEN** it is absent from durable learning records and the conversation mirror

#### Scenario: Attach a practice draft explicitly

- **WHEN** a learner sends an Agent turn while a practice draft exists
- **THEN** the focused draft, chosen options, and visible image references are available to that turn without creating an attempt

#### Scenario: Agent reads the focused answer

- **WHEN** the learner is viewing an open problem with entered work and sends a chat message
- **THEN** the current problem and entered work take priority in Agent context while wider workspace reads remain available
