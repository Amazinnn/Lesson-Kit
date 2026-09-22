## MODIFIED Requirements

### Requirement: Step-level stuck marking

For open-ended or multi-step problems, the practice page SHALL present the
solution as blocks and let the learner mark "stuck at block N" with an optional
natural-language note. The marking SHALL be recorded on the explicit attempt
and SHALL be available in authoritative Agent conversation context for that
problem. Marking is never required.

#### Scenario: Mark a stuck step in a proof

- **WHEN** the learner records "stuck at step 3" with a short note on a proof problem
- **THEN** the attempt stores the marker and note and later Agent context for that problem includes them

### Requirement: Answer text capture for open problems

The practice page SHALL provide an answer box for open problem types and SHALL
store the learner's text only on an explicit rated attempt. The latest recorded
answer SHALL be available to authoritative Agent conversation context.

#### Scenario: Attach a design attempt to its record

- **WHEN** the learner submits a design answer with an explicit rating
- **THEN** the attempt stores the answer text and later Agent context includes it

### Requirement: Unified Agent data CLI

The workbench SHALL expose JSON data commands for get, list, search, history,
create, update, delete, and current-state replacement across knowledge points,
formal problems, and knowledge relations. Read operations SHALL perform zero
writes. Candidate entities, candidate gates, and candidate promotion SHALL NOT
exist; governed content enters through the Check pipeline.

#### Scenario: Search without a write

- **WHEN** an Agent searches the pool through `lesson-kit data`
- **THEN** matching current entities are returned and no content or learning row changes

#### Scenario: Candidate command is unavailable

- **WHEN** an Agent requests a candidate entity or promotion command
- **THEN** the CLI rejects the unsupported entity/action instead of recreating candidate state

#### Scenario: Edit a candidate

- **WHEN** an Agent requests an update for a retired candidate entity
- **THEN** the CLI rejects the unsupported entity and no pool row changes

#### Scenario: Promote a gated candidate

- **WHEN** an Agent requests retired candidate promotion
- **THEN** the CLI rejects the unsupported action and points to the Check pipeline

### Requirement: Readable content sequences

New knowledge points, formal problems, relations, and ingest batches SHALL use
course/chapter-scoped sequential readable identifiers. Existing suffixes seed
the next value; no hash-derived identifier is used.

#### Scenario: Allocate after existing content

- **WHEN** a scope already contains numbered entities and a new entity is created
- **THEN** it receives the next readable number without reusing a deleted id

### Requirement: Semantic graph attraction

The live graph model SHALL expose each knowledge point's formal-problem count
and importance and each semantic edge's explicit strength, shared-formal-
problem count, and computed attraction. Only formal problems contribute to
problem counts. Edges originate only from formal relations or existing
`related_kp_ids`; co-occurrence never invents an edge.

#### Scenario: Count formal problems per node

- **WHEN** formal problems refer to a knowledge point
- **THEN** `problem_count` includes those formal problems and no retired candidate source

#### Scenario: Merge a bidirectional semantic edge

- **WHEN** two knowledge points declare duplicate or reverse semantic relations
- **THEN** the graph model returns one edge for the unordered pair

#### Scenario: Reinforce an existing relation with shared problems

- **WHEN** two related knowledge points share formal problems
- **THEN** their edge reports the shared count and higher computed attraction

#### Scenario: Do not infer a relation from co-occurrence

- **WHEN** two knowledge points share a problem but have no formal relation
- **THEN** the graph model returns no edge between them
