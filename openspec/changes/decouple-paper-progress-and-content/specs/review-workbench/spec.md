## MODIFIED Requirements

### Requirement: Paper-backed Practice Run
A Practice Run SHALL execute one already determined Paper and preserve its ordered item identities. Viewing, answering, skipping, rating, scheduling or Agent discussion SHALL NOT dynamically pull extra items into it. At most one selected active run exists per workspace execution resource, but each saved Paper MAY retain its own unfinished execution independently. Switching selection SHALL pause rather than abandon the previous Paper and SHALL NOT require completing it first. Only explicit governed content edits/deletion under this change may alter or reset unfinished execution state; those are not scheduler-driven assembly.

A Paper SHALL NOT be defined by one product-level content-mode choice. Each item SHALL use its actual validated answering type. Existing `practice_mode` fields MAY remain compatibility metadata but SHALL NOT force every item into the same form or recreate a dynamic queue. Rating preference controls feedback timing only. Displaying, drafting, revealing, skipping or ending work SHALL NOT manufacture learning evidence. Scheduling SHALL never lock an item.

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

### Requirement: Practice Run interruption recovery
Recorded learning conclusions SHALL remain durable. Each saved Paper's unfinished checkpoint SHALL durably preserve source identity, fixed ordered items, cursor, completion states and unsubmitted answer/choice drafts across navigation, refresh and browser/service restart. Selecting another Paper SHALL NOT clear it. Draft persistence SHALL NOT create an attempt, verdict, feedback, signal, learning-progress or schedule entry. Submitted evidence and completed historical runs SHALL NOT be reconstructed from drafts or markers.

#### Scenario: Resume the same Paper after refresh
- **WHEN** the learner refreshes or leaves and returns to an unfinished Paper
- **THEN** its own fixed items, execution progress and unsubmitted answer/choice drafts are restored without repeating assembly

#### Scenario: Recorded results survive browser closure
- **WHEN** the learner closes the browser after recording results and reopens the workspace later
- **THEN** recorded results and every saved Paper's surviving unfinished checkpoint remain available, with only the selected Paper active

#### Scenario: Unsubmitted browser state creates no record
- **WHEN** the tab ends with an unsubmitted draft, note, reveal state or rating
- **THEN** no learning evidence is fabricated; supported answer/choice drafts are preserved as execution state only

## ADDED Requirements

### Requirement: Question corrections reset only affected unfinished items
Changing a question's stem/embedded answering content, options, answer key or answering type SHALL retain its identity and Paper memberships/order, reset only that question to pending in unfinished Paper executions, and discard only its stale answer/choice drafts. Other items' progress SHALL survive. Explanation/title/KP/difficulty/source-only changes and no-op edits SHALL NOT trigger reset. Historical attempts/ratings/runs SHALL remain historical and SHALL NOT be automatically regraded. A submit made against superseded Paper structure or answering content SHALL be rejected before any learning write, with a recoverable explanation.

#### Scenario: Correct a shared question's answer key
- **WHEN** question Q occurs in unfinished A/B and its answer key changes
- **THEN** only Q becomes pending in both, its old drafts are cleared, other items retain progress, and prior attempts/ratings remain unchanged

#### Scenario: Edit only explanation or metadata
- **WHEN** Q's explanation, title, knowledge-point labels, difficulty or source metadata changes without changing answering content
- **THEN** neither its completion marker nor its draft is reset and a current answer is not rejected solely for that metadata change

#### Scenario: Old page submits after correction
- **WHEN** an old page submits an answer after its question's answering content or Paper structure was superseded
- **THEN** it receives an explicit stale-content response and no attempt, feedback, signal or schedule effect is written

### Requirement: Question deletion preserves unrelated execution progress and history
Deleting a question SHALL clean its current memberships and unfinished item/draft references, but SHALL preserve every other item's state and every genuine historical attempt/rating/run. This SHALL be an explicit exception to full progress reset after a manual Paper membership edit. Cursors SHALL resolve to a surviving item; removing the last item SHALL NOT fabricate completion or learning evidence. Historical reads SHALL indicate deleted content without requiring an active question.

#### Scenario: Delete a question shared by multiple unfinished Papers
- **WHEN** Q is deleted from the pool while A/B both reference it
- **THEN** Q disappears from both current memberships/checkpoints, all other progress survives, and previous historical evidence stays readable as deleted content
