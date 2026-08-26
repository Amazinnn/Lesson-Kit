## MODIFIED Requirements

### Requirement: Session interruption recovery

Recorded learning conclusions SHALL remain durable in the pool. The active practice mode, current problem, seen-problem set, and unified-rating queue SHALL remain tab-scoped in the existing browser session storage and SHALL be restored after refresh or page navigation in the same tab. Closing the tab MAY end unsubmitted active-session state and SHALL NOT manufacture a durable learning record.

#### Scenario: Resume after refreshing practice

- **WHEN** the learner refreshes or leaves and returns to practice in the same tab
- **THEN** the selected mode, current problem, seen-problem set, and pending unified ratings are restored without pulling a duplicate problem

#### Scenario: Recorded results survive browser closure

- **WHEN** the learner closes the browser after submitting ratings and later reopens the workspace
- **THEN** those recorded results remain in the pool and are reflected in later ordering

#### Scenario: Resume after closing the browser

- **WHEN** the learner closes the browser mid-session and later reopens the workspace
- **THEN** recorded results are intact and practice can begin from current pool state without inventing records for the closed tab's unfinished actions

#### Scenario: Unsubmitted state creates no record

- **WHEN** the browser tab ends with a draft, skipped item, or pending unsubmitted rating
- **THEN** no attempt, feedback, signal, progress, or schedule row is added for that unfinished action

## ADDED Requirements

### Requirement: Action-oriented learning reminders

Student-facing surfaces SHALL NOT expose raw signal types, weights, weakness scores, scheduler state, repetitions, ease, or manual three-state mastery controls. An item with explicit current weakness evidence SHALL display `重点练习`; otherwise an item that is due SHALL display `可以复习`; all other items SHALL remain neutral. The underlying evidence, scheduling, and compatibility APIs SHALL remain available to ordering and Agent context.

#### Scenario: Show an explicit weakness action

- **WHEN** a knowledge point has current explicit weakness evidence
- **THEN** its student-facing reminder is `重点练习` without raw signal or scheduler parameters

#### Scenario: Show only a due reminder

- **WHEN** an item has no current explicit weakness evidence and is due
- **THEN** its student-facing reminder is `可以复习` without claiming mastery

#### Scenario: Keep an unevidenced item neutral

- **WHEN** an item has neither current weakness evidence nor a due review
- **THEN** no mastery claim or internal state label is shown

### Requirement: Formal problems are reveal-ready

Every formal problem eligible for practice SHALL have a non-empty gated solution. A formal pool update SHALL NOT expose a partially solved batch.

#### Scenario: Reveal a formal problem solution

- **WHEN** the learner reveals any formal problem in the active pool
- **THEN** a non-empty solution that passed the formal content gates is available
