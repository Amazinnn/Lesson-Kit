## ADDED Requirements

### Requirement: Imported answers populate Paper progress without starting a run

A saved Paper read SHALL surface a parked execution created by attempt import as
its unfinished progress, using the same ordered-item, content-revision, Paper
generation, item-availability, and current-manifest validation as any other
checkpoint. Import-created progress SHALL NOT appear as an archived practice run
until the learner explicitly submits it. Starting the Paper SHALL resume the
imported progress rather than create a new execution or reset it.

#### Scenario: Imported progress is visible in the saved Paper list

- **WHEN** an import creates or updates a saved Paper's parked progress
- **THEN** the Paper's saved record reports the updated completed and total counts without an archived run

#### Scenario: Starting resumes imported progress

- **WHEN** the learner starts a Paper whose parked progress contains imported answers
- **THEN** the existing ordered items, imported states, attempt links, and remaining pending items are restored

#### Scenario: Stale imported progress is not offered

- **WHEN** the saved Paper's items, revisions, or generation no longer match the imported checkpoint
- **THEN** the Paper reports continuation unavailable with a reason and no imported state is silently remapped

### Requirement: Missing Paper items may be appended explicitly

An explicit `papers append` SHALL append one existing pool problem to the end of
a saved Paper while preserving every existing item's order, state, attempt link,
draft, and unfinished progress. It SHALL increment the Paper's structural
generation, update the matching active or parked execution's Paper generation,
and add one pending item at the end. It SHALL NOT use the manual
membership/order update path that resets progress. It SHALL be idempotent: an
already present problem SHALL return `already_present` without writing. It SHALL
refuse an unknown problem, an invalid or unavailable Paper, or a checkpoint that
cannot be validated.

#### Scenario: Append a missing problem without resetting progress

- **WHEN** an exact existing problem is appended to a partially practised Paper
- **THEN** existing items keep their states, attempts, and drafts, and one pending item is added at the end

#### Scenario: Append updates a parked checkpoint

- **WHEN** the target Paper has packed progress and another Paper is selected
- **THEN** the parked checkpoint gains the pending item and the selected Paper is untouched

#### Scenario: Repeat the same append

- **WHEN** the same problem is appended to the same Paper twice
- **THEN** the second call reports `already_present` and writes nothing

#### Scenario: Append refuses an unknown or duplicate identity

- **WHEN** the problem does not exist or is already in the Paper at another position
- **THEN** no content, execution, or progress row changes

## MODIFIED Requirements

### Requirement: Paper is the Practice Run boundary

A Practice Run SHALL execute a frozen Paper, never a live knowledge-point query.
Knowledge points, learner evidence, filters, and Agent instructions MAY constrain
Paper assembly, but once execution begins they SHALL NOT silently add, remove, or
replace items in that run. The only exception is an explicit `papers append` of a
problem that was missing from the saved container: it appends at the end and
preserves existing progress, as defined by the missing-item append requirement.
Historical callers that label assembly origin as `quick`, `practice_set`, or
`agent` MAY be accepted during migration; every newly persisted active execution
and run archive SHALL normalize that origin to `paper`. Replaying a historical
run SHALL likewise create a new Paper-sourced execution from the archived fixed
items.

#### Scenario: Knowledge-point entry assembles before execution

- **WHEN** the learner requests Agent/CLI authoring for one knowledge point
- **THEN** that knowledge point constrains Paper assembly, and the Practice Run begins only after the Paper's item list is fixed

#### Scenario: Old quick caller is normalized

- **WHEN** a compatibility caller submits a fixed item list labelled `quick`
- **THEN** the new active execution stores `source_kind = paper` and does not preserve `quick` as a peer execution type

#### Scenario: Replaying old history upgrades the execution source

- **WHEN** an archived run created under `quick`, `practice_set`, or `agent` is replayed
- **THEN** the exact archived items are reused and the new execution stores `source_kind = paper`

#### Scenario: Explicit repair append is not silent assembly

- **WHEN** a caller explicitly appends one missing problem to an existing Paper
- **THEN** the Paper gains that problem at the end while its existing items and progress remain unchanged

Learner pages SHALL manage and practise existing Papers without manual item selection, condition-based assembly or membership/order editing. Agent/CLI authoring SHALL retain existing scope, filter, exact-id and save contracts.

### Requirement: Paper practice presentation state remains independent

Each ordinary-problem Paper's unfinished run SHALL independently retain Answer
Reveal Timing, ordered items, position, inputs, stuck marks, submission locks,
reference-view facts and self-ratings. Switching Paper, pausing, refreshing or
restarting browser/service SHALL restore confirmed state without clearing another
Paper. Timing SHALL remain fixed until completion. Completed answer sheets SHALL
remain associated with original runs rather than reconstructed from new runs or
current drafts. Existing stale content/container validation SHALL continue;
restoration SHALL NOT silently remap unavailable problems or override an
approved reset. An explicit append SHALL preserve every existing item's state,
attempt link, and draft and add one pending item at the end; an open browser
session that carries the previous Paper generation SHALL be rejected as stale
and must reload before writing.

#### Scenario: Switch Papers and reload
- **WHEN** the learner partly fills A in whole-Paper mode, answers B in per-item mode, reloads and returns to A
- **THEN** both retain separate choices, positions, inputs, locks, marks and ratings without new runs or implicit submission

#### Scenario: Container changes after saving input
- **WHEN** a content or structure revision invalidates a saved practice write
- **THEN** existing stale-write/reset rules apply and the UI reports readiness without silently losing input or claiming successful submission

#### Scenario: A repeated Paper has two answer sheets
- **WHEN** a completed Paper is started again
- **THEN** new progress cannot overwrite the previous answer sheet or self-ratings

#### Scenario: Append invalidates an open session
- **WHEN** a problem is appended while a browser session still holds the previous Paper generation
- **THEN** the next write from that session is rejected as stale and the reloaded Paper shows the pending appended item
