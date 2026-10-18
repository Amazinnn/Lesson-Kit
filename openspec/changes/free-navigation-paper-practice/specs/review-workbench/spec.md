## MODIFIED Requirements

### Requirement: Paper-backed Practice Run
A Practice Run SHALL execute one already determined Paper and preserve its ordered item identities. Viewing, answering, skipping, rating, scheduling or Agent discussion SHALL NOT dynamically pull extra items into it. At most one selected active run exists per workspace execution resource, but each saved Paper MAY retain its own unfinished execution independently. Switching selection SHALL pause rather than abandon the previous Paper and SHALL NOT require completing it first. Only explicit governed content edits/deletion under this change may alter or reset unfinished execution state; those are not scheduler-driven assembly.

A Paper SHALL NOT be defined by one product-level content-mode choice. Each item SHALL use its actual validated answering type. Existing `practice_mode` fields MAY remain compatibility metadata but SHALL NOT force every item into the same form or recreate a dynamic queue. Self-rating preference controls learning feedback only; Answer Reveal Timing separately controls result disclosure and answer locking. Displaying, drafting, revealing, skipping or ending work SHALL NOT manufacture learning evidence. Scheduling SHALL never lock an item.

#### Scenario: Start from an assembled Paper
- **WHEN** a Paper's ordered items are fixed and the learner starts it
- **THEN** those exact items become the Practice Run and no later scope or scheduler change mutates it

#### Scenario: Skip an item without a learning record
- **WHEN** the learner skips the current item without an explicit recorded conclusion
- **THEN** execution advances by the existing skip rules and no learner-state row is manufactured

#### Scenario: Explicit rating records a learning conclusion
- **WHEN** the learner submits a 1–5 self-rating for a completed problem
- **THEN** feedback, derived learner state and schedule persist exactly once

#### Scenario: Off-mode verdict remains compatible
- **WHEN** an objective item uses compatibility rating mode `off`
- **THEN** its recorded verdict derives the existing learning conclusion exactly once without synthesizing a rating event

#### Scenario: Agent records only at the learner's request
- **WHEN** the learner asks the Agent to record the active answer
- **THEN** only the explicit attempt command records it; viewing or discussing the draft alone does not

#### Scenario: Switch between unfinished Papers
- **WHEN** Paper A is partly completed and the learner starts or resumes Paper B, then returns to A
- **THEN** both retain independent unfinished progress, A resumes its own cursor/items/drafts, and no run is marked abandoned or completed merely by switching

### Requirement: Durable practice run archive

The single active-practice resource SHALL remain the execution authority for one
Paper-backed Practice Run. Every newly created execution SHALL use the product
source semantic `paper`; historical `quick`, `practice_set`, or `agent` source
values MAY remain readable as migration data, and replaying such history SHALL
create a new Paper-sourced execution from the archived fixed items.

When the learner explicitly submits the Paper, or a run is explicitly replaced or cleared, the workbench SHALL
append one minimal `practice_runs` snapshot before deleting active execution
state. The snapshot SHALL preserve Paper source identity/reference/label, ordered
item identities and final states, rating compatibility metadata, timestamps, and the submitted per-item answer references and presentation state needed to reopen the completed answer sheet. It SHALL NOT replace, duplicate, edit, or delete `problem_attempts` or
`feedback_events`.

#### Scenario: Completing the last item archives the run

- **GIVEN** the learner has explicitly requested final Paper submission
- **WHEN** the final pending item of an active Paper is answered or marked stuck
- **THEN** one completed snapshot is appended and active execution is cleared exactly once as part of that explicit submission
- **AND** answering the last item outside explicit final submission does not archive the run

#### Scenario: Replacing an unfinished run keeps both histories honest

- **WHEN** the learner explicitly replaces an unfinished Paper run
- **THEN** the old run is archived as abandoned, its existing attempts remain unchanged, and the new Paper starts independently

#### Scenario: Replay legacy history through the Paper boundary

- **WHEN** a historical run labelled `quick`, `practice_set`, or `agent` is replayed
- **THEN** its archived item order is reused but the new active execution stores the Paper source semantic

### Requirement: Practice Run interruption recovery
Recorded learning conclusions SHALL remain durable. Each saved Paper's unfinished checkpoint SHALL durably preserve source identity, fixed ordered items, cursor, Answer Reveal Timing, submission locks, reference-view facts, stuck marks, completion states, self-ratings and unsubmitted answer/choice drafts across navigation, refresh and browser/service restart. Selecting another Paper SHALL NOT clear it. Draft persistence SHALL NOT create an attempt, verdict, feedback, signal, learning-progress or schedule entry. Submitted evidence and completed historical runs SHALL NOT be reconstructed from drafts or markers.

#### Scenario: Resume the same Paper after refresh
- **WHEN** the learner refreshes or leaves and returns to an unfinished Paper
- **THEN** its own fixed items, execution progress and unsubmitted answer/choice drafts are restored without repeating assembly

#### Scenario: Recorded results survive browser closure
- **WHEN** the learner closes the browser after recording results and reopens the workspace later
- **THEN** recorded results and every saved Paper's surviving unfinished checkpoint remain available, with only the selected Paper active

#### Scenario: Unsubmitted browser state creates no record
- **WHEN** the tab ends with an unsubmitted draft, note, reveal state or rating
- **THEN** no learning evidence is fabricated; supported inputs and presentation state are preserved as execution state only, and already confirmed ratings remain durable
## ADDED Requirements

### Requirement: Explicit final Paper submission

Only explicit `提交试卷` SHALL finish an ordinary-problem run. Final submission SHALL submit every existing nonblank input not already submitted, mark remaining blank items stuck, freeze final answers and archive one completed run. It SHALL NOT ask for an additional blank-item confirmation or wait for self-rating. Previously submitted items SHALL not create duplicate Attempts, feedback or learning effects. A whole-Paper editable draft or revisable stuck mark SHALL NOT become an immutable Attempt before final submission. Per-item explicit submissions and locked stuck marks SHALL use the existing submission/evidence flow; navigation and draft saving SHALL never create evidence.

Submission SHALL be retry-safe and validate execution, Paper generation and item content revisions. A failed submission SHALL retain recoverable input and show failure rather than show completion. A lost response SHALL be resolvable without resubmitting evidence or archiving again. Existing immutable historical Attempts SHALL NOT be rewritten to emulate editable drafts.

#### Scenario: Submit filled and blank items
- **WHEN** a run is finally submitted with saved inputs, some unsubmitted multiple-choice/text answers and some blank items
- **THEN** filled inputs are submitted as answers, only blank items become stuck, and the run completes without a second confirmation or mandatory rating

#### Scenario: Last per-item result is not final submission
- **WHEN** the last pending item receives a per-item answer or stuck submission
- **THEN** the learner may still browse the run and only explicit final submission archives it

#### Scenario: Retry after a lost final response
- **WHEN** the same final submission is retried after its response is lost
- **THEN** the original completed result is recovered without duplicate Attempts, feedback, learning effects or run snapshots

#### Scenario: Failed or stale submission
- **WHEN** final submission fails or a referenced revision is stale
- **THEN** no successful completion is claimed and saved input remains recoverable under the existing revision/reset rules
