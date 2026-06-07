# Source Scope

| field | value |
|---|---|
| task_scope |  |
| course |  |
| chapter_or_task |  |
| source_files |  |
| requested_range |  |
| full_coverage_claim | yes / no / limited |
| output_target | first_pass_lesson |
| final_artifact_name | （科目名） （第X章） （章名） 速览.md |
| excluded_source_range |  |
| deferred_source_range |  |
| missing_or_uncertain_sources |  |
| blocking_source_issues |  |

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

This file fails if it is a placeholder, if the source boundary is unclear, if excluded or uncertain source ranges are hidden, or if the order rule cannot be audited by later files.

It must preserve source facts without analysis, identify missing or uncertain evidence, state whether full coverage is claimed, and provide enough source-unit detail for `knowledge-points.md` and `coverage-check.md` to audit coverage.
