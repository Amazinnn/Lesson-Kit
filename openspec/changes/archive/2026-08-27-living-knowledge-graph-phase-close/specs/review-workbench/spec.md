## MODIFIED Requirements

### Requirement: Semantic graph attraction

The live graph model SHALL expose each knowledge point's formal-problem count and existing importance classification, and each semantic edge's explicit strength, shared-formal-problem count, and computed attraction. Edges SHALL originate only from formal knowledge relations or existing `related_kp_ids`. Reverse duplicate edges SHALL be merged, and shared problems SHALL reinforce but SHALL NOT create semantic edges.

#### Scenario: Count formal problems per node

- **WHEN** formal and candidate problems refer to a knowledge point with an existing importance value
- **THEN** `problem_count` includes only formal problems and the graph node reports that importance value

#### Scenario: Merge a bidirectional semantic edge

- **WHEN** two knowledge points relate to each other through duplicate or reverse relation declarations
- **THEN** the graph model returns one edge for that unordered pair

#### Scenario: Reinforce an existing relation with shared problems

- **WHEN** two related knowledge points share formal problems
- **THEN** their edge reports the shared count and higher computed attraction

#### Scenario: Do not infer a relation from co-occurrence

- **WHEN** two knowledge points share a problem but have no formal relation or `related_kp_ids` link
- **THEN** the graph model returns no edge between them
