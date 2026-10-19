## MODIFIED Requirements

### Requirement: Paper assembly engine

The pull engine SHALL assemble the ordered problem portion of a Paper from an
explicit knowledge-point scope, conditional source/difficulty filters, and
learner evidence such as weak, due, or previously wrong items. Assembly SHALL be
a read operation with zero learning writes. When durable problems are exhausted,
it SHALL report the shortage per knowledge point instead of inventing content.
Every selected problem SHALL carry the reason it entered the Paper.

Exact problem ids supplied by an Agent or CLI authoring workflow SHALL be
included in the Paper when they resolve to existing durable problems, with
reason `explicit`, even when they fall outside the requested scope or filters or
exceed the requested problem count. This exact-id capability is an authoring
primitive, not a learner-facing practice control: the browser SHALL NOT expose a
per-problem picker or scope/filter/quantity assembly controls. Browser Paper-list management SHALL not edit item membership or order; authoring through Agent/CLI remains available.

#### Scenario: Assemble a Paper for one weak knowledge point

- **WHEN** the learner asks the Agent to use one weak knowledge point as the requested practice scope
- **THEN** the engine assembles durable problems for a Paper constrained to that scope and reports the selection reasons before execution begins

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested for the Paper
- **THEN** the assembly result lists the shortfall per knowledge point and points to the Check pipeline instead of fabricating problems

#### Scenario: Agent pins an exact problem while authoring

- **WHEN** an Agent or CLI authoring workflow supplies an exact id for an existing durable problem while composing a Paper
- **THEN** the Paper SHALL include that problem with reason `explicit`, even if it falls outside the requested scope or filters or exceeds the requested problem count, without creating a learner-side manual-pick affordance

#### Scenario: Learner evidence guides assembly

- **WHEN** Paper assembly is driven by weak knowledge points, due problems, or previously wrong problems
- **THEN** the returned problems reflect that evidence and each carries the matching reason

### Requirement: Re-assembly after wrong results

A wrong or stuck result MAY be discussed with the Agent to request authoring a new Paper from relevant knowledge scope or learning evidence. It SHALL NOT expose a learner-operated assemble-similar button. The completed or
running Paper SHALL never be extended in place, and the follow-up SHALL not
silently inherit an old seen-id queue as its execution identity.

#### Scenario: Build a follow-up Paper after a wrong answer

- **WHEN** a problem is answered wrong or stuck and the learner asks the Agent to author similar material
- **THEN** Lesson Kit assembles a new Paper from the relevant scope/evidence and starts it only after its item list is determined

### Requirement: Chapter lens scoping

The chapter lens SHALL scope reading surfaces — knowledge-point list/detail,
knowledge graph, and practice suggestions — and MAY provide the default scope for
Paper Assembly. It SHALL NOT define or mutate the contents of a running Paper.
An explicitly chosen Paper-assembly scope MAY span chapters and SHALL survive
chapter-lens changes in the same tab until an explicit Agent/CLI authoring request changes that scope.

#### Scenario: Lens narrows default assembly suggestions

- **WHEN** one chapter is active and the learner has not established another explicit assembly scope
- **THEN** practice suggestions and default Paper Assembly use that chapter without creating an executable knowledge-point queue

#### Scenario: Explicit scope survives lens changes

- **WHEN** the learner has explicitly requested an Agent/CLI assembly scope spanning chapters and changes the reading lens
- **THEN** the selected assembly scope remains unchanged while the reading surfaces follow the new lens

Reading-lens and graph selection controls SHALL remain reading controls and SHALL NOT accumulate a learner-managed Paper Assembly scope.

## REMOVED Requirements

### Requirement: Source filter panel on the practice page
**Reason**: Learner-operated source/condition assembly is retired.
**Migration**: Keep Agent/CLI/API filter semantics and read-only facets; remove the learner panel and stale browser selections without executing an assembly or modifying a saved Paper.
