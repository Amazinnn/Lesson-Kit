# practice-experience Specification

## Purpose

Store one optional, learner-owned practice-experience summary under each knowledge point: reusable problem-solving lessons distilled from practice rather than a log of mistakes. The summary is editable by the learner or an Agent acting on an explicit request, may cite representative formal problems already linked to that knowledge point, and uses revision checks so concurrent edits never silently overwrite each other.

## Requirements

### Requirement: One optional experience summary per knowledge point

A knowledge point MAY have one practice-experience summary. No database row SHALL be created merely because the knowledge point exists. An absent summary SHALL render as an empty state that can be created later. A stored summary SHALL contain non-empty Markdown content, a positive integer revision, its last editor (`user` or `agent`), and timestamps.

#### Scenario: Knowledge point has no experience yet

- **WHEN** a learner opens a knowledge point with no stored practice experience
- **THEN** the page shows `暂无经验总结` and an action to create one, and no empty experience row is manufactured

#### Scenario: Create the first summary

- **WHEN** the learner explicitly saves non-empty practice experience for a knowledge point with no existing summary
- **THEN** one summary is created at revision 1 and becomes visible under that knowledge point

### Requirement: Experience supports explicit CRUD

The workbench SHALL expose create, read, update, and delete operations for practice experience. Browser edits SHALL be attributed to `user`; Agent-facing CLI edits SHALL be attributed to `agent`. The installed Agent command surface SHALL be `lesson-kit experience <workspace> <get|create|update|delete> <kp-id>`, with create/update payloads supplied as JSON and update/delete requiring the revision that was read. Deleting an experience SHALL delete only its summary and representative-problem links, never the knowledge point, formal problem, attempt, feedback, signal, or schedule.

#### Scenario: Edit an existing summary

- **WHEN** an editor submits a valid update against the current revision
- **THEN** the Markdown and representative-problem links are replaced atomically and the revision increases by one

#### Scenario: Delete an experience

- **WHEN** an editor explicitly deletes the current experience using its current revision
- **THEN** the summary and its representative-problem links disappear while all formal learning content and learning records remain intact

### Requirement: Concurrent writes never silently overwrite

Create, update, and delete SHALL run in an immediate SQLite transaction. Update and delete SHALL require the revision the editor read. If the stored revision differs, the operation SHALL fail with a conflict and leave the stored summary and links unchanged. Browser HTTP update/delete SHALL surface the stale revision as HTTP 409.

#### Scenario: Two editors save from the same revision

- **WHEN** the learner and Agent both read revision 7 and the learner saves first
- **THEN** the learner write becomes revision 8 and the Agent's later revision-7 write is refused without overwriting it

### Requirement: Representative problems are references, not a new relation layer

An experience MAY cite zero or more representative formal problems. Every cited problem SHALL already list the owning knowledge point in `problems.kp_ids`; otherwise the write SHALL be refused. The link SHALL store only the problem id and ordering position. Display SHALL resolve the current problem `display_title`, falling back to the current problem text when no display title exists, so titles are never duplicated into experience storage.

If a later formal problem mutation removes the owning knowledge point from `problems.kp_ids`, the now-invalid representative-problem link SHALL be removed automatically. This invariant SHALL apply regardless of which problem mutation path performed the edit.

#### Scenario: Cite a problem already linked to the knowledge point

- **WHEN** an experience update cites a formal problem whose `kp_ids` contains that knowledge point
- **THEN** the reference is accepted and the current problem title is shown with the experience

#### Scenario: Reject a foreign problem

- **WHEN** an experience update cites a problem that is not formally linked to that knowledge point
- **THEN** the whole update is refused and no experience content or link changes

#### Scenario: Formal relation is removed later

- **WHEN** a cited problem is edited so that its `kp_ids` no longer contains the experience's knowledge point
- **THEN** that representative-problem reference is removed without deleting the experience summary or changing the formal problem beyond the requested edit

### Requirement: Knowledge-point UI owns the experience editor

The knowledge-point page SHALL render practice experience before the complete linked-problem list. Existing experience SHALL render with the shared safe Markdown subset and show its representative problems by current readable title. The editor SHALL allow the learner to replace the Markdown and choose zero or more already-linked representative problems. An absent experience SHALL remain an empty state until saved.

#### Scenario: Edit from the browser

- **WHEN** the learner enters edit mode on an existing experience
- **THEN** the current Markdown and representative-problem selections are editable, save uses the displayed revision, cancel writes nothing, and a revision conflict asks the learner to refresh rather than silently replacing the newer version

### Requirement: Experience is distinct from knowledge content and learner signals

Practice experience SHALL NOT be stored in `knowledge_points.body`, `fragile`, feedback notes, or `learner_signals`. It records reusable solving experience, not curriculum truth and not a weakness score. Existing mastery, weakness, scheduling, and problem-selection rules SHALL ignore experience unless a future specification explicitly changes them.

#### Scenario: Add experience without changing learning state

- **WHEN** a learner creates or edits practice experience
- **THEN** no attempt, feedback, learner signal, current learning state, or schedule row is created or modified

### Requirement: Agent context includes the current experience

Authoritative knowledge-point Agent context SHALL include the current practice-experience summary and its representative problems when present. Ordinary conversation SHALL remain read-only; an Agent mutation requires the learner's explicit request and the explicit `lesson-kit experience` write command.

#### Scenario: Discuss an existing experience

- **WHEN** the learner asks the Agent about a knowledge point that already has practice experience
- **THEN** the Agent context contains that current summary and its cited problem identities and readable titles without creating or changing any row
