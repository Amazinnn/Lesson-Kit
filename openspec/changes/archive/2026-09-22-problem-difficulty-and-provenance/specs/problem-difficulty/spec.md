## ADDED Requirements

### Requirement: Complete lazy difficulty vector

A formal problem or micro quiz MAY have no objective difficulty rating. A
rated problem SHALL store integer 1-5 values for knowledge breadth, reasoning
depth, transfer distance, and construction openness together with one derived
REAL total and model id. These six values SHALL be all absent or all present.
Missing difficulty SHALL NOT block ingest, display, practice, or scheduling.

#### Scenario: Unrated problem remains usable

- **WHEN** a problem has no difficulty vector
- **THEN** it remains visible and practiceable and no default score is invented

#### Scenario: Partial vector is refused

- **WHEN** a rating manifest omits one dimension or supplies a value outside 1-5
- **THEN** the complete rating batch fails and no problem rating changes

### Requirement: Versioned deterministic total

The model `cognitive-v1-equal-mean` SHALL compute the equal arithmetic mean of
the four dimensions and round half up to one decimal. A caller SHALL NOT set
the total or model id.

#### Scenario: Quarter mean rounds half up

- **WHEN** the dimensions are 2, 2, 2, and 3
- **THEN** the stored total is 2.3 and the model id is `cognitive-v1-equal-mean`

#### Scenario: Three-quarter mean rounds half up

- **WHEN** the dimensions are 2, 2, 3, and 4
- **THEN** the stored total is 2.8

### Requirement: Cross-type dimension rubric

The four dimensions SHALL be rated independently of answer format. Knowledge
breadth SHALL describe the necessary knowledge structure rather than raw
knowledge-point count. Reasoning depth SHALL describe the shortest reliable
solution rather than answer length. Transfer distance SHALL range from direct
example isomorphism to method reconstruction in new conditions. Construction
openness SHALL range from one bounded answer to incomplete constraints that
require justified trade-offs. Each dimension SHALL use these anchors:

| Score | Knowledge breadth | Reasoning depth | Transfer distance | Construction openness |
|---|---|---|---|---|
| 1 | One local fact or concept | Recall, recognition, or one direct substitution | Isomorphic to a definition or worked example | Selection, judgement, or one unique short answer |
| 2 | One concept plus a direct prerequisite, or two same-section points | One standard transformation or calculation | Only values, wording, or surface context change | Bounded calculation or short explanation |
| 3 | Two or three same-chapter concepts cooperate | Dependent steps including one method choice | Representation or combination is unfamiliar but the method family is clear | Goal is fixed but several valid paths exist |
| 4 | Several concepts across sections | Multi-stage reasoning that organizes intermediate results and methods | No method cue; the solver must identify and adapt one | Proof, modelling, or design contains a substantive choice |
| 5 | Cross-chapter or cross-framework synthesis | Subgoals and methods must be planned and may require backtracking | Method must be generalized or reconstructed for new conditions or a new domain | Constraints are incomplete and alternatives must be weighed and justified |

#### Scenario: Format does not determine rating

- **WHEN** a routine proof uses one local concept and one standard transformation
- **THEN** its proof problem type does not force a high reasoning or openness score

#### Scenario: Stored knowledge ids do not determine breadth

- **WHEN** one necessary concept is represented by several closely related knowledge-point ids
- **THEN** breadth follows the required knowledge structure rather than the raw id count

### Requirement: Explicit rating transaction

The CLI SHALL expose `lesson-kit difficulty <workspace> check|apply --input
<file|->`. One manifest MAY contain one or many problems. Check SHALL perform
zero writes; apply SHALL validate the whole manifest and overwrite all named
ratings in one transaction.

#### Scenario: Check previews without writing

- **WHEN** a valid rating manifest is checked
- **THEN** computed totals are returned and database contents are unchanged

#### Scenario: One invalid item protects the batch

- **WHEN** any item in an apply manifest is invalid or unknown
- **THEN** none of the named problem ratings changes

### Requirement: Rating invalidation on content change

Changing a problem's text, solution, knowledge-point membership, or problem
type SHALL clear its complete objective rating. The problem remains usable and
is not automatically rerated.

#### Scenario: Edit a rated problem

- **WHEN** an explicit content update changes the problem text
- **THEN** all difficulty fields become null and the problem remains in the pool

### Requirement: Explicit difficulty filtering

Pull MAY carry total or per-dimension ranges and an optional balanced strategy.
Without such arguments, selection order SHALL remain unchanged. Explicit
ranges exclude unrated rows; ordinary selection retains them.

#### Scenario: Ordinary pull is compatible

- **WHEN** no difficulty filter or strategy is supplied
- **THEN** the same ordered problem ids are returned as before this capability

#### Scenario: Balanced pull retains unrated fallback

- **WHEN** balanced selection exhausts rated bands before reaching the requested count
- **THEN** unrated eligible problems may fill the remainder after rated rows

### Requirement: Objective and learner difficulty remain separate

Objective difficulty SHALL NOT be overwritten or inferred from ratings,
signals, due state, attempts, or learner condition. Learner evidence continues
to choose knowledge scope and priority only.

#### Scenario: Low self-rating does not rewrite the vector

- **WHEN** a learner rates a problem 1
- **THEN** learning state and scheduling update while the objective vector is unchanged
