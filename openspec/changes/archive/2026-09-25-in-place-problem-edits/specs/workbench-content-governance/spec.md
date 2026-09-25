## ADDED Requirements
### Requirement: In-place problem patch

Content that already exists SHALL be changeable without deleting and
re-importing it, because a problem's readable id is its identity and every
attempt, rating, and schedule hangs off it. A patch SHALL name existing problems
only, SHALL refuse unknown ids, unknown field names, an id outside the
workspace's course, and any attempt to change the id, and SHALL keep difficulty
ratings a separate command. It SHALL be available as one explicit command per
problem and as one bulk manifest (`problem-patch`) that prevalidates every item,
records one readable batch id with the manifest snapshot **and each row's
previous values**, writes one recoverable backup, and applies in one
transaction: any invalid item leaves the pool untouched. Rolling such a batch
back SHALL restore the previous values instead of deleting rows, so the
learner's records survive an edit and its reversal. A patch SHALL resolve the
practice mode from the payload unless the caller declares it, SHALL validate the
resulting row against the micro-quiz contract for the parts it touches, and
SHALL NOT re-validate untouched legacy fields. Unknown field names SHALL be an
error rather than a silent drop.

#### Scenario: One problem is edited explicitly

- **WHEN** the learner or the Agent patches one existing problem with new attributes
- **THEN** exactly that row changes in one transaction, its id and its learning records are untouched, and the result reports the written fields

#### Scenario: A bulk patch is all or nothing

- **WHEN** a `problem-patch` manifest mixes valid items with an unknown id, an unknown field, or a contract violation
- **THEN** every reason is reported per item and no row, batch record, or backup changes state

#### Scenario: A patch is rolled back value for value

- **WHEN** an applied `problem-patch` batch is rolled back
- **THEN** every touched column returns to exactly its previous value, including cleared difficulty ratings, and the rows themselves remain

#### Scenario: Unsupported fields are refused

- **WHEN** a patch payload carries a field the pool does not manage, or a difficulty field
- **THEN** it is refused with the writable field list (or the `lesson-kit difficulty` pointer) and nothing is written
