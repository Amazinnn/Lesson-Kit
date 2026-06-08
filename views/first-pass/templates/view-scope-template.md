# View Scope — First Pass

This file defines the VIEW scope (what to render and how), NOT the extraction scope. The source material has already been extracted into the pool. This file captures student intent and confirms configuration before any analysis or rendering begins.

| field | value |
|---|---|
| view_name | first-pass |
| task_scope |  |
| course |  |
| chapter_or_task |  |
| source_files |  |
| pool_source | pool/knowledge/kp-query-result.json |
| requested_range |  |
| full_coverage_claim | yes / no / limited |
| output_target | first_pass_lesson |
| final_artifact_name | （科目名） （第X章） （章名） 速览.md |
| excluded_source_range |  |
| deferred_source_range |  |
| missing_or_uncertain_sources |  |
| blocking_source_issues |  |

## Student Intent

### Natural Language Request

<!-- Agent: record student's exact words here -->
[Student's original request, e.g., "快速扫一遍第 2 章，重点看卡诺图，不要题目"]

### Agent-Parsed Intent

<!-- Agent: structured breakdown of what the student wants -->

| Dimension | Parsed Value |
|-----------|---------------|
| KP scope | full / sections [X-Y] |
| MCQ inclusion | yes / no / selective |
| Depth preference | standard / lighter / deeper |
| Section priority | [list priority sections or "none"] |
| Custom constraints | [any special rules] |

## Configuration Confirmation

<!-- Agent fills "Agent Recommendation" column based on progress data and pool content.
     Presents to student for confirmation.
     Student may override any field.
     config_confirmed MUST be checked before proceeding to 02_analysis. -->

| Configuration Field | Agent Recommendation | Student Confirmed |
|---------------------|---------------------|-------------------|
| view_type | first-pass | |
| course | [course abbreviation] | |
| chapter | [chapter id] | |
| scope | [full / sections X-Y] | |
| mcq_inclusion | [yes / no / selective] | |
| depth_override | [standard / lighter / deeper] | |
| section_priority | [list or "none"] | |
| additional_constraints | [any custom rules] | |

- [ ] **config_confirmed** — Student has explicitly confirmed this configuration.

  **DO NOT proceed to 02_analysis until this box is checked.** If the Student Intent section is empty or config_confirmed is unchecked, this file FAILS its minimum completion standard.

## Source Range Table

| source_unit_id | source_location | source_unit_name | included | required_status | order_rule | notes |
|---|---|---|---|---|---|---|
| su-001 |  |  | yes / no / uncertain | required / optional / extension | preserve / local_reorder / implementation_chain |  |

## Triggered Source Features

| feature | present | evidence_location | handling_decision |
|---|---|---|---|
| visual_dependent_content | yes / no / uncertain |  | knowledge_points_and_final_markdown / triggered_inventory |
| code_pseudocode_algorithm_trace | yes / no / uncertain |  | knowledge_points_and_final_markdown / triggered_inventory |
| lab_system_implementation_artifact | yes / no / uncertain |  | knowledge_points_and_final_markdown / triggered_inventory |
| source_examples_or_exercises | yes / no / uncertain |  | knowledge_points_and_final_markdown / triggered_inventory / ignore_for_first_pass |

## Minimum Completion Standard

This file fails if:
- It is a placeholder with unfilled fields
- The Student Intent section is empty (no natural language request recorded)
- The config_confirmed checkbox is unchecked
- The source boundary is unclear (excluded or uncertain source ranges are hidden)
- The order rule cannot be audited by later files (`03_plans/structure-plan.md`, `04_checks/coverage.md`)
- The Configuration Confirmation table has unfilled Agent Recommendation fields
- Pool source (`pool/knowledge/kp-query-result.json`) is not referenced

It must preserve source facts without analysis, identify missing or uncertain evidence, state whether full coverage is claimed, capture student intent before any analysis begins, and provide enough source-unit detail for `03_plans/structure-plan.md` and `04_checks/coverage.md` to audit coverage.

The final artifact name must follow the naming convention in `STYLE.md`.
