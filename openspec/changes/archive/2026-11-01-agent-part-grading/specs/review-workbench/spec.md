## MODIFIED Requirements

### Requirement: Grading input modes

Machine-gradable choice and true/false content SHALL retain its existing automatic verdict. Open problems SHALL retain answer, reveal and optional learner self-rating while explicit subjective submission requests external Agent grading of that exact response. Grading SHALL separate final-answer and process conclusions according to agent-part-grading, and SHALL obey independent Answer Reveal Timing. The learner SHALL also be able to ask an Agent to transcribe and grade through the attempt CLI. Missing learning ratings SHALL NOT block recording or regress the schedule. Subjective grading SHALL NOT synthesize self-ratings or automatically update learning projections. AI unavailability SHALL NOT block saving an answer or continuing practice.

#### Scenario: Auto-grade a choice problem
- **WHEN** the learner submits an answer for a machine-gradable problem through its configured submission control
- **THEN** the system grades it correct or wrong and records the graded attempt under the existing objective rules

#### Scenario: Reveal-then-rate an open problem
- **WHEN** the learner submits text for an open problem
- **THEN** the response is saved, Agent grading is requested, references and grading follow the reveal policy, and optional self-rating retains the existing learning effects

#### Scenario: Record without grading
- **WHEN** the learner or Agent records an answer without a learning rating
- **THEN** the attempt is retained without subjective grading itself changing signals, current states, progress or schedule

### Requirement: Answer text capture for open problems

The practice page SHALL provide one editable response area per subjective part, or one for an unsplit open problem. Explicit submission SHALL persist that response regardless of whether self-rating or Agent grading succeeds. Learner-requested Agent attempt CLI calls SHALL continue to support transcription. The exact submitted response and its part identity SHALL be available to later authoritative Agent context. Drafts MAY persist in existing execution checkpoints but SHALL NOT become Attempts before submission. Extracted Answers SHALL be separately maintained by Agent operations and SHALL NOT overwrite the learner response.

#### Scenario: Attach a design attempt to its record
- **WHEN** the learner submits a design answer with an explicit rating
- **THEN** the attempt stores its original text, the rating follows its existing contract and later Agent context includes the submitted response

#### Scenario: Agent transcribes a photographed answer
- **WHEN** the learner asks the Agent to record a photographed open answer
- **THEN** later Agent context can read the transcription without a stored answer-image attachment

#### Scenario: Save while grading is unavailable
- **WHEN** a learner submits a subjective response without a rating and the grading provider is unavailable
- **THEN** the original response is durable and available to Agent context independently of the grading failure

### Requirement: Durable attempt records for every surface

Every submitted answer SHALL become a durable, append-only attempt regardless of the browser, CLI or Agent surface. A browser objective attempt SHALL store response text, chosen option texts and the objective verdict when a usable key exists. A subjective attempt SHALL store the original response with its legacy objective verdict empty; separate versioned Part Grading Results SHALL hold subjective conclusions. Structured-part submissions SHALL preserve the owning problem, stable part and content version; separate submissions of different parts SHALL NOT be mistaken for duplicate attempts. Retrying the same submission SHALL return its original result. Whole-problem and final-Paper submission SHALL NOT duplicate already submitted parts.

An attempt alone SHALL NOT move learning projections except for existing independent objective off-mode behavior. Existing explicit rating SHALL link back through a validated `attempt_id`. Subjective grading and composite status counts SHALL NOT produce automatic problem-level learning effects. Old pools SHALL retain the existing degraded legacy answer-recording path, without manufacturing part structure or conclusions; new structured grading requires the explicit additive migration.

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
