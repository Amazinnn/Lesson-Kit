## Purpose

Agent learning evidence gives the external teaching Agent a small, read-only, human-readable view of recorded learner history when a question requires historical support.

## Requirements

### Requirement: Knowledge-point evidence is bounded and readable

Lesson Kit SHALL expose a read-only knowledge-point evidence query that returns the knowledge point plus a bounded newest-first set of recorded problem attempts under that knowledge point. Each returned attempt SHALL include readable problem text and the learner outcome fields that are actually available, such as answer text or selected choices, status/verdict, linked rating/feedback, and attempt time.

Internal problem and attempt ids MAY be included for provenance, but they SHALL NOT be the only evidence returned.

#### Scenario: Ask whether a mistake happened before

- **WHEN** the Agent queries evidence for a knowledge point with recorded attempts
- **THEN** one bounded read returns recent attempted problem text together with concrete learner outcomes, without requiring the Agent to fan out through every related problem id

### Requirement: Evidence reads do not infer learner traits

The evidence query SHALL return recorded facts and SHALL NOT itself label the learner as weak, careless, improving, or otherwise infer a learning pattern. Historical conclusions remain the teaching Agent's responsibility and must be proportional to the evidence it actually read.

#### Scenario: One historical mistake exists

- **WHEN** only one relevant failed attempt is returned
- **THEN** the data interface reports that attempt as evidence and does not manufacture a repeated-error or weakness conclusion

### Requirement: Evidence reads are zero-write operations

Reading learning evidence SHALL NOT create or modify attempts, feedback, signals, current learning state, schedules, practices, content, or the workspace database file. The Data query and installed CLI SHALL reject a missing or non-file database before connecting to SQLite.

#### Scenario: Agent inspects history

- **WHEN** the Agent reads knowledge-point evidence during an ordinary tutoring turn
- **THEN** all managed learner and content state remains unchanged

#### Scenario: Workspace database is missing

- **WHEN** the Data query or installed CLI is given a registered workspace whose database path is absent or is not a regular file
- **THEN** the read fails before connecting and leaves that path absent or unchanged

### Requirement: Evidence volume is explicitly bounded

The installed CLI SHALL default to 8 recent evidence rows, SHALL accept integer limits from 1 through 20, and SHALL reject invalid or excessive limits rather than silently returning an unbounded history dump. The result SHALL report whether older evidence exists.

#### Scenario: Default evidence read

- **WHEN** the Agent runs `lesson-kit evidence <workspace> kp <kp-id>` without a limit
- **THEN** Lesson Kit returns at most 8 recent evidence rows and reports whether older evidence exists
