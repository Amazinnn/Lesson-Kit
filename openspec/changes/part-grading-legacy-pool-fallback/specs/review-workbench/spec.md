## MODIFIED Requirements

### Requirement: Durable attempt records for every surface

Every submitted answer SHALL become a durable, append-only attempt regardless
of the browser, CLI or Agent surface. A browser objective attempt SHALL store
response text, chosen option texts and the objective verdict when a usable key
exists. A subjective attempt SHALL store the original response with its legacy
objective verdict empty; separate versioned Part Grading Results SHALL hold
subjective conclusions. Structured-part submissions SHALL preserve the owning
problem, stable part and content version; separate submissions of different
parts SHALL NOT be mistaken for duplicate attempts. Retrying the same
submission SHALL return its original result. Whole-problem and final-Paper
submission SHALL NOT duplicate already submitted parts.

An attempt alone SHALL NOT move learning projections except for existing
independent objective off-mode behavior. Existing explicit rating SHALL link
back through a validated `attempt_id`. Subjective grading and composite status
counts SHALL NOT produce automatic problem-level learning effects. Old pools
SHALL retain the existing degraded legacy answer-recording path, without
manufacturing part structure or conclusions; new structured grading requires
the explicit additive migration.

A pool that has not received that additive migration SHALL keep working end to
end rather than fail on the new storage: opening or refreshing a practice run
SHALL present its items with no part grading requested and no grading
conclusions, and an explicit subjective submission SHALL record the attempt
through the pre-migration attempt columns only, without writing part context or
grading-job rows. Explicit part-grading requests on such a pool SHALL fail with
an actionable migration message and zero writes; they SHALL NOT silently
succeed, fabricate conclusions, or surface as an internal server error. The
migration gap SHALL be observable from the product's own read-only diagnostics.

#### Scenario: A browser answer is durable

- **WHEN** the learner submits a subjective response on the practice page
- **THEN** one attempt stores the original response, separate grading may follow, and no learning projection changes merely because grading is requested

#### Scenario: The rating links back

- **WHEN** an explicit rating is recorded for a submitted attempt
- **THEN** feedback carries that exact validated attempt id and the attempt reads back with its rating

#### Scenario: A mismatched attempt id is refused

- **WHEN** a rating names an attempt belonging to another target
- **THEN** the rating is refused with zero writes

#### Scenario: Submit remaining parts without duplicates

- **WHEN** part A is already submitted and the learner submits the remaining parts together, then retries after a lost response
- **THEN** A's attempt is unchanged and each remaining submitted part has exactly one new attempt, with the retry returning the original outcome

#### Scenario: Practice status on an unmigrated pool

- **WHEN** a practice run on a pool without the additive part-grading schema is opened or refreshed
- **THEN** its items render with no part grading requested, no grading conclusions and no server error, exactly like the legacy whole-problem path

#### Scenario: Submit on an unmigrated pool

- **WHEN** the learner explicitly submits a subjective answer on a pool without the additive schema
- **THEN** the attempt is recorded through the pre-migration columns only, the paper keeps advancing, and no part context or grading-job row is invented

#### Scenario: Explicit grading on an unmigrated pool

- **WHEN** an Agent or CLI asks for part grading on a pool without the additive schema
- **THEN** the request fails with a message naming the migration command, writes nothing, and is not reported as an internal server error
