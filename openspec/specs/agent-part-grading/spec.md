# agent-part-grading Specification

## Purpose

Support mixed-type problem parts and asynchronous Agent grading of a single learner-authored response, preserving original submissions while presenting independent final-answer and reasoning conclusions.

## Requirements

### Requirement: Authored problem parts have stable identities

An Agent authoring or organizing a formal problem SHALL be able to save an ordered set of parts with stable identities, prompts, answering types and optional reference material. A problem SHALL support yes/no, single-choice, multiple-choice, calculation and proof/open-response parts in one item. Practice SHALL use the saved structure rather than infer or reorder parts during an execution. A problem without parts SHALL remain answerable as one legacy whole problem. Governed later edits SHALL use existing content-version invalidation rules for affected unfinished work and SHALL NOT rewrite historical submissions.

#### Scenario: Author a mixed problem
- **WHEN** an Agent saves a problem containing a yes/no part, a multiple-choice part and a calculation part
- **THEN** practice renders all three in saved order with their appropriate controls and stable part identities

#### Scenario: Open an unsplit legacy problem
- **WHEN** a learner opens an existing problem without structured parts
- **THEN** the problem remains answerable as a whole and is not automatically split or reordered

### Requirement: Subjective parts have one learner input

Each subjective part SHALL expose exactly one editable learner response area containing the learner's answer and reasoning. After submission, an Agent SHALL be able to maintain an optional Extracted Answer as a separate read-only display. Extracted Answers SHALL represent only the learner's submitted content and SHALL NOT replace it or be filled from the reference answer. Proofs and responses without a concise final result SHALL omit the Extracted Answer display. Missing final results SHALL be shown as unprovided rather than wrong or inferred.

#### Scenario: Grade a calculation response
- **WHEN** a learner submits reasoning ending with a numerical result
- **THEN** the original response remains intact and an Agent-provided Extracted Answer can be shown beside the reference answer without another learner-editable answer box

#### Scenario: Grade a proof
- **WHEN** the part requires a proof whose process is the answer
- **THEN** the view presents submitted reasoning, available reference reasoning and process feedback without an artificial short-answer field

### Requirement: Submission requests recoverable Agent grading

Explicit subjective submission SHALL durably save the response before requesting grading through the configured external Agent. The submission SHALL authorize grading that exact response, not arbitrary content or learning-state mutation. Practice SHALL remain usable without an available Agent. Grading failures SHALL preserve the saved response and expose retry without creating another Attempt. Retrying the same submission or grading operation SHALL NOT duplicate writes. A delayed result SHALL remain attached to the original execution, problem, part, submission and content version, even after navigation or Paper switching. Stale or invalid results SHALL NOT replace current results.

#### Scenario: Agent is unavailable
- **WHEN** a subjective response is accepted but the Agent cannot run
- **THEN** the response remains saved, grading is truthfully pending or failed with a reason, and the learner can continue and retry later

#### Scenario: Navigate during grading
- **WHEN** grading for part A finishes after the learner moves to part B
- **THEN** only A's grading is updated and B's draft, answer and selection remain unchanged

### Requirement: Answering status has independent dimensions

Answering Status SHALL distinguish unprovided, draft and submitted responses; an explicit stuck mark SHALL be preserved independently. Grading progress SHALL distinguish not requested, pending, running, completed and failed. Completed grading SHALL separately carry final-answer and process conclusions. Final-answer conclusions SHALL distinguish correct, wrong, needs confirmation and unprovided; process conclusions SHALL distinguish correct, partially correct, wrong, needs confirmation and unprovided. Inapplicable dimensions SHALL be omitted. Proof parts SHALL use only process conclusions. A failed grading operation SHALL NOT be represented as a wrong answer or as an uncertain academic conclusion. Subjective parts SHALL NOT receive a synthesized overall verdict.

#### Scenario: Correct result with flawed reasoning
- **WHEN** the Agent finds a correct final answer and an incorrect process
- **THEN** the part shows answer correct and process wrong separately without collapsing them into a total verdict

#### Scenario: Partial reasoning without a result
- **WHEN** the learner provides some valid reasoning but no final result
- **THEN** the part can show process partially correct and answer unprovided, without treating the missing result as a wrong value

### Requirement: Stuck marks preserve and permit process feedback

An explicit `不会` action SHALL retain any written response and the separate stuck mark, disclose available reference material for that part, and allow the Agent to comment on and grade existing reasoning. A missing learner result SHALL remain unprovided even after reference disclosure. Completing grading SHALL NOT silently erase the stuck mark. A blank stuck response SHALL NOT be fabricated into a learner answer.

#### Scenario: Ask for help after partial work
- **WHEN** the learner writes part of a derivation and activates `不会`
- **THEN** the partial work and stuck mark remain, available reference material is shown, and process feedback can coexist with answer unprovided

### Requirement: Agent grading is revisable without rewriting attempts

Explicit Agent operations SHALL support reading, creating, revising and withdrawing Extracted Answers and Part Grading Results. The learner-facing product SHALL expose them read-only; correction requests SHALL use the Agent conversation. Mutations SHALL require the exact target, the expected current revision and an operation identity, validate atomically, and preserve a revision history including withdrawals. Withdrawn results SHALL no longer count as current conclusions. Ordinary explanation SHALL remain read-only; grading submissions and explicit review requests provide the specific write intent. Authorized accepted changes SHALL appear in an open view without restarting, while preserving drafts, focus, cursor, scroll position and reveal rules.

#### Scenario: Correct an extraction through conversation
- **WHEN** the learner asks the Agent to fix an extracted value and the Agent submits a valid revision
- **THEN** the read-only value and its conclusions update, the original response remains unchanged, and both the previous and current grading revisions remain inspectable

#### Scenario: Reject an obsolete revision
- **WHEN** two grading operations target the same expected revision and one has already succeeded
- **THEN** the second conflicting write is refused without overwriting the accepted result or changing other submissions

#### Scenario: Withdraw a conclusion
- **WHEN** an authorized Agent withdraws the current result using its expected revision
- **THEN** the current view returns to an ungraded state, stops counting the withdrawn conclusion, and retains the withdrawal history and original response

### Requirement: Reference provenance and uncertainty are explicit

When no usable reference answer or proof exists, the Agent SHALL be allowed to independently derive a reference for the grading result, clearly labelled as Agent-derived rather than source-provided. Such a derivation SHALL NOT silently replace authored source answers. Insufficient evidence SHALL yield needs confirmation, with an explanation and a conversation review path, rather than a fabricated definitive judgment. Grading SHALL distinguish the learner's Extracted Answer, the reference result and the derivation's provenance.

#### Scenario: Independently derive a reference
- **WHEN** a submitted calculation lacks source reference material and the Agent derives a reference result
- **THEN** the view identifies that reference as Agent-derived and preserves any existing authored source content

#### Scenario: Cannot establish correctness
- **WHEN** the Agent cannot reliably assess a submitted proof
- **THEN** the process conclusion is needs confirmation, the response remains saved and review remains available

### Requirement: Subjective grading does not synthesize learning effects

Creating, revising or withdrawing subjective grading SHALL NOT automatically create a 1–5 Self-Rating or change mastery, learner signals, current learning state or review schedules. Existing explicit evaluation mechanisms SHALL retain their effects. Independently submitted legacy objective items SHALL retain existing verdict behavior. A mixed parent SHALL NOT derive a total learning conclusion from counts of part results; objective-part grading alone SHALL NOT multiply problem-level learning effects.

#### Scenario: Revise wrong to correct
- **WHEN** an Agent revises a subjective final-answer conclusion from wrong to correct
- **THEN** current grading and review filters update without an automatic learning projection or schedule write
