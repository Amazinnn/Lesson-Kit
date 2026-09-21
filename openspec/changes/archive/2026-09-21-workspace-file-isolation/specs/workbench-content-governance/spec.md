## ADDED Requirements

### Requirement: Ingest stays inside one course

An ingest batch SHALL belong to exactly one course: the course of the workspace's
pool. Content ids in a `micro-quiz-patch` or `flash-card-patch` manifest SHALL
carry that course prefix, and a batch whose ids carry another course SHALL be
refused by the gate with an itemized reason naming the expected prefix. A
`figure-patch` manifest SHALL name the workspace's own course and a chapter that
is a plain identifier, and its figure paths SHALL resolve inside the workspace's
`.lessonkit/figures/<course>/<chapter>/` directory; a manifest whose course or
chapter would leave that directory SHALL be refused and no file SHALL be written.

#### Scenario: A foreign-course id is refused

- **WHEN** a micro-quiz or flash-card manifest carries ids prefixed by a course other than the workspace's
- **THEN** the gate fails with an itemized reason naming the expected prefix and nothing is written

#### Scenario: A figure patch cannot leave its course folder

- **WHEN** a figure-patch manifest names a course other than the workspace's, or a chapter containing a path separator or `..`
- **THEN** the gate fails and no figure file is written outside `.lessonkit/figures/<workspace course>/<chapter>/`

#### Scenario: Same-course content still applies

- **WHEN** a manifest carries the workspace's own course prefix and a valid chapter
- **THEN** the batch passes the same deterministic gates as before and applies as one recorded batch

#### Scenario: A batch with no active course is refused

- **WHEN** a manifest is applied to a workspace whose registry entry has no active course
- **THEN** the gate fails with an explicit reason instead of guessing a prefix
