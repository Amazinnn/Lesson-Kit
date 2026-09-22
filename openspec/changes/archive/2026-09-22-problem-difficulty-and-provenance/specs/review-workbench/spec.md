## ADDED Requirements

### Requirement: Provenance-filtered problem pull

Problem pull SHALL accept `source_kind`, `origin_kind`, and a derived mutually
exclusive `source_group`. `ai_generated` contains generated origin; `exam`
contains non-generated quiz/midterm/final/makeup sources; `textbook` contains
non-generated textbook sources; all remaining rows are `other`. Multiple
filters intersect.

#### Scenario: AI exam-grounded problem stays in AI group

- **WHEN** a generated problem is grounded in final-exam material
- **THEN** the AI group includes it and the exam convenience group does not

#### Scenario: Combine source axes

- **WHEN** pull requests textbook material and adapted origin
- **THEN** only rows satisfying both values are returned
