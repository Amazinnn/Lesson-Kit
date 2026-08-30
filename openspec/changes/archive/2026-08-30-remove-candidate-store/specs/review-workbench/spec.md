## MODIFIED Requirements

### Requirement: Problem pull engine

The pull engine SHALL return problems linked to the requested knowledge points,
ordered for weakness, with repeat practice in the same session de-prioritized.
When durable problems are exhausted it SHALL report the shortage per knowledge
point instead of inventing content; no candidate staging exists to fall back on.

#### Scenario: Pull problems for a weak knowledge point

- **WHEN** the user starts practice for a selected weak knowledge point
- **THEN** the engine returns durable problems for that point, weakness-ordered, with none repeated within the same session

#### Scenario: Pool shortage is reported

- **WHEN** a knowledge point has fewer durable problems than requested
- **THEN** the response lists the shortfall per knowledge point and the UI points to the Check pipeline as the content path instead of fabricating problems

### Requirement: Past-paper coverage gate

Extraction inputs SHALL include past exam papers, and a machine-readable
coverage contract (`01_inputs/past-paper-coverage.json`) SHALL map every exam
point to a pool knowledge point or durable problem. The coverage gate SHALL
fail with the list of unmapped exam points when any point lacks a mapping, and
the workbench SHALL surface unmapped exam points as pool gaps eligible for the
Check ingest path.

#### Scenario: Every exam point is mapped

- **WHEN** the coverage gate runs and all exam points map to pool items
- **THEN** the gate passes and no gap is reported

#### Scenario: An exam point is unmapped

- **WHEN** an exam point has no mapping to any knowledge point or durable problem
- **THEN** the gate fails, the unmapped point is listed, and the workbench shows it as a pool gap with a Check ingest entry point
