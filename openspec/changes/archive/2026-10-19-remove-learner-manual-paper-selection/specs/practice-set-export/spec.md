## MODIFIED Requirements

### Requirement: Paper is the Practice Run boundary

A Practice Run SHALL execute a frozen Paper, never a live knowledge-point query.
Knowledge points, learner evidence, filters, and Agent instructions MAY constrain
Paper assembly, but once execution begins they SHALL NOT silently add, remove, or
replace items in that run. Historical callers that label assembly origin as
`quick`, `practice_set`, or `agent` MAY be accepted during migration; every newly
persisted active execution and run archive SHALL normalize that origin to
`paper`. Replaying a historical run SHALL likewise create a new Paper-sourced
execution from the archived fixed items.

#### Scenario: Knowledge-point entry assembles before execution

- **WHEN** the learner requests Agent/CLI authoring for one knowledge point
- **THEN** that knowledge point constrains Paper assembly, and the Practice Run begins only after the Paper's item list is fixed

#### Scenario: Old quick caller is normalized

- **WHEN** a compatibility caller submits a fixed item list labelled `quick`
- **THEN** the new active execution stores `source_kind = paper` and does not preserve `quick` as a peer execution type

#### Scenario: Replaying old history upgrades the execution source

- **WHEN** an archived run created under `quick`, `practice_set`, or `agent` is replayed
- **THEN** the exact archived items are reused and the new execution stores `source_kind = paper`

Learner pages SHALL manage and practise existing Papers without manual item selection, condition-based assembly or membership/order editing. Agent/CLI authoring SHALL retain existing scope, filter, exact-id and save contracts.
