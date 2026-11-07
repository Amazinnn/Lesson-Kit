## Purpose

Defines the observable 诊断、针对性练习与复习接线 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.

## ADDED Requirements

### Requirement: Learning targets drive existing content selection

The learning workflow SHALL use the stated target, course range and observed evidence to prioritize relevant existing questions and past papers. Supplementary generated items SHALL carry truthful provenance and unresolved questionable mappings SHALL be excluded.

#### Scenario: The learner specifies a weakness

- **WHEN** the course has relevant verified questions and unrelated questions
- **THEN** the selected practice addresses the weakness and does not require broad untargeted practice

### Requirement: Diagnosis is bounded by task and evidence

A focused weakness session SHALL begin with a small diagnostic step. A full new chapter SHALL support distributed coverage that can accumulate fifteen to twenty-five items and shrink with sufficient evidence or limited time. Item count SHALL NOT become a mechanical prerequisite.

#### Scenario: The learner wants short targeted practice

- **WHEN** historical evidence already identifies likely weak content
- **THEN** the workflow moves quickly to representative practice without repeating a full chapter test

#### Scenario: The chapter is new

- **WHEN** core coverage needs several groups of diagnostic questions
- **THEN** the diagnostic proceeds in bounded groups and avoids repeated low-value questions

### Requirement: Evidence and learning judgments stay distinct

The workflow SHALL distinguish unfamiliar knowledge, inability to apply knowledge, uncertainty, revealed answers and unsupported conclusions. User correction SHALL directly change the next practice arrangement while retaining original answers and observations.

#### Scenario: The learner corrects a diagnosis

- **WHEN** the user says the diagnosed weakness is wrong
- **THEN** subsequent practice follows the corrected target without rewriting original attempts

#### Scenario: An answer was guessed or revealed

- **WHEN** the evidence contains a guessed success or a post-reveal answer
- **THEN** the workflow does not claim independent stable mastery from that evidence

### Requirement: Hints and continuity respect learner progress

Help SHALL begin with minimal requested hints and deepen only as needed. The workflow SHALL preserve mainline and return position across interruptions, adjust to actual time and exam goals, and close at natural interaction points.

#### Scenario: The learner asks an interruption question

- **WHEN** a temporary branch is resolved
- **THEN** the workflow returns to its recorded mainline position

#### Scenario: Time is limited

- **WHEN** the declared budget reaches a natural stopping point
- **THEN** the learner can continue or finish with saved position and next action

### Requirement: Review uses legitimate persisted evidence

Follow-up review SHALL use existing legitimate feedback and scheduling writers and remain adjustable. Appropriate reassessment can reuse recent questions, and independent new items SHALL measure transfer. LLM unavailability SHALL leave independently supported ordinary practice usable.

#### Scenario: The model is unavailable

- **WHEN** existing questions can be selected and answered without model output
- **THEN** ordinary practice remains usable and model-only actions are truthfully incomplete

#### Scenario: Review is planned

- **WHEN** an exercise ends with valid learning evidence
- **THEN** the established scheduling rules consume that evidence without fabricating a learner self-rating
