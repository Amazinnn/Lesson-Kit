## MODIFIED Requirements

### Requirement: Paper-backed Practice Run
A Practice Run SHALL execute one already determined Paper and preserve its ordered item identities. Viewing, answering, skipping, rating, scheduling or Agent discussion SHALL NOT dynamically pull extra items into it. An explicit `papers append` of a problem that was missing from the saved container is a governed content edit; it MAY extend the running Paper at the end without changing existing item states or drafts. At most one selected active run exists per workspace execution resource, but each saved Paper MAY retain its own unfinished execution independently. Switching selection SHALL pause rather than abandon the previous Paper and SHALL NOT require completing it first. Only explicit governed content edits/deletion under this change may alter or reset unfinished execution state; those are not scheduler-driven assembly.

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

#### Scenario: Explicit repair append extends the running Paper
- **WHEN** the learner explicitly appends one missing problem to the running Paper
- **THEN** the Paper gains a pending item at the end while every existing item keeps its state, draft, attempt link and cursor meaning

### Requirement: Re-assembly after wrong results

A wrong or stuck result MAY be discussed with the Agent to request authoring a new Paper from relevant knowledge scope or learning evidence. It SHALL NOT expose a learner-operated assemble-similar button. Outside the explicit repair append defined by `practice-set-export`, the completed or running Paper SHALL never be extended in place, and the follow-up SHALL not silently inherit an old seen-id queue as its execution identity.

#### Scenario: Build a follow-up Paper after a wrong answer

- **WHEN** a problem is answered wrong or stuck and the learner asks the Agent to author similar material
- **THEN** Lesson Kit assembles a new Paper from the relevant scope/evidence and starts it only after its item list is determined

#### Scenario: Repair append is not a follow-up Paper

- **WHEN** the learner supplies a missing problem that belongs to the Paper's source material
- **THEN** the existing Paper gains that problem at the end; a new assembled Paper is not created

### Requirement: Durable attempt records for every surface

Every submitted answer SHALL become a durable, append-only attempt row regardless
of the surface that produced it — the browser practice flow, the CLI, or an
Agent manifest. A browser-submitted attempt SHALL store the answer text, the
chosen option texts when the item has options, and the objective verdict when
the item carries a usable answer key; a comprehensive answer SHALL store its
text with no verdict. An attempt row alone SHALL NOT move learning progress,
schedule, signals, or current state; those still move only through the rating
flow, which SHALL link its event back to the attempt (`attempt_id`) after
validating that the attempt belongs to the rated item. Paper execution progress
MAY move when an explicit import names a `paper_id` and binds the attempt to
that Paper's active or parked execution. A pool that predates the columns SHALL
still accept the attempt (degraded, without verdict or choices) instead of
failing the practice flow.

#### Scenario: A browser answer is durable

- **WHEN** the student submits an answer on the practice page
- **THEN** one attempt row persists the answer text, the chosen options, and the objective verdict, and no learning projection changes until the rating lands

#### Scenario: The rating links back

- **WHEN** the session's rating is recorded for an item that submitted an attempt
- **THEN** the feedback event carries that attempt's id, and the attempt reads back with its rating

#### Scenario: A mismatched attempt id is refused

- **WHEN** a rating names an attempt that belongs to another item
- **THEN** the rating is refused with zero writes

#### Scenario: Submit remaining parts without duplicates

- **WHEN** part A is already submitted and the learner submits the remaining parts together, then retries after a lost response
- **THEN** A's attempt is unchanged and each remaining submitted part has exactly one new attempt, with the retry returning the original outcome

#### Scenario: An imported attempt moves only Paper execution progress

- **WHEN** an ungraded attempt is imported with a `paper_id`
- **THEN** the named Paper's item state and attempt link change, while learning progress, signals, current states and schedule remain unchanged
