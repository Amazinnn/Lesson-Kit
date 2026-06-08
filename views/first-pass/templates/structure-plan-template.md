# First Pass Structure Plan

## Pool Data Mapping

The KP data comes from the SQLite pool (loaded via `pool/knowledge/kp-query-result.json`), NOT from re-extracting the source. This template defines how pool fields map to plan columns.

| Pool Field | Plan Column | Usage |
|-----------|-------------|-------|
| `kp_id` | `kp_id` | Direct copy — internal reference only, NEVER shown to student |
| `knowledge_item` | `student_visible_title` (starting point) | Transform: "布尔代数基本定理" → "**布尔代数的基本定理**" or a more descriptive title |
| `learning_action` | `question_target` (informational) | "区分X和Y" → target is about boundary/contrast judgment; "应用Z" → target is about condition recognition |
| `knowledge_type` | multi-angle framing choice | `concept-property` → definition angle; `method-modeling` → operational angle; `formula-calculation` → condition+formula angle |
| `difficulty` | question difficulty selection | Match question difficulty to KP difficulty (±1 level) |
| `fragile` | extra attention flag | `fragile=1` → must add boundary note in quick_absorption, must have MCQ (even in "selective" mode) |
| `related_kp_ids` | through-line input | Fed to `skills/through-line-selection.md` |
| `confused_state` | MCQ trigger (selective mode) | If confused_state is flagged, this KP gets a Q. block even when MCQ=selective |

## Section Structure Plan

| final_section_id | final_section_title | source_unit_basis | kp_ids | purpose | rendering_rule |
|---|---|---|---|---|---|
| fs-001 |  | su-001 | course-source-ch03-kp-001 | source_grounded_first_pass | preserve_source_order / local_dependency_adjustment / implementation_chain |

## KP-Level Rendering Plan

| kp_id | final_section_id | student_visible_title | writing_view_primary | writing_view_secondary | rendering_intent | quick_absorption | question_target | question_form | question_draft | answer_key | answer_explanation | answer_block_group | forbidden_rendering |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| course-source-ch03-kp-001 | fs-001 |  |  |  |  | quick absorption: clean definition/formula statement + one through-line accent sentence choosing a recurring angle; do not write a standalone summary | scene_judgment / concept / condition / boundary / relation | single-choice / true-false / short judgment |  |  | one short sentence | section-end answer block | no kp_id; no knowledge_type; no writing_view; no template labels; no exam-prep framing |

Rules:

- `quick_absorption` is a clean definition/formula statement plus one through-line accent sentence that chooses a recurring angle from the chapter's knowledge relationship analysis. The through-line selected in `02_analysis/through-line-selection.md` MUST appear in every KP's quick_absorption sentence. If a KP has no apparent connection to the through-line, document why in the `forbidden_rendering` column. The final lesson may polish it lightly but must not expand it into a mini-lesson or standalone summary.
- `question_draft`, `answer_key`, `answer_explanation`, and `answer_block_group` must be planned here before final rendering.
- `question_form` must use single-choice with 4 options for scene_judgment questions. True/false is acceptable for condition/boundary checks only.
- Checkpoint questions must follow the Source-Dependency Self-Check Protocol in `skills/scene-judgment-mcq.md`.
- Checkpoint questions must not require calculation, proof, code writing, or real operation. Even for algorithm, code, system, or lab items, ask only for recognition, condition, boundary, structure, variable/step role, or next-step judgment.
- Each checkpoint question should require returning to the corresponding source section to answer confidently; it should not be answerable from the quick_absorption statement alone and should not resemble an exam or textbook exercise.
- `answer_explanation` must stay short, normally one sentence, and must not become a standard-answer routine.
- `forbidden_rendering` must explicitly block internal fields, source-absent umbrella terms, formalistic templates, and exam-prep framing.

## Config-Driven Column Rules

When the student's config (from `01_inputs/view-scope.md` Configuration Confirmation) modifies MCQ inclusion:

| Config value | Rule |
|-------------|------|
| "no MCQ" | `question_target`, `question_draft`, `answer_key`, `answer_explanation` marked "—" (not applicable). Do NOT delete the columns — coverage check needs to see all KPs are accounted for. |
| "selective" | Only `fragile=1` and `confused_state` KPs have filled question columns. Other KPs marked "—". |
| "yes" | All KPs get filled question columns. |

**Important:** Never delete the question columns from the table, regardless of config. The coverage check in `gates/coverage.md` requires all KPs to be present with all columns — empty columns are valid, missing columns mean an incomplete plan.

## Ordering Decision

| decision_field | value |
|---|---|
| ordinary_source_order | preserve / not_applicable |
| local_dependency_adjustment | none / stated_below |
| implementation_chain_ordering | no / yes |
| forbidden_reordering |  |
| justification |  |

## Explanation Boundary

| rule | value |
|---|---|
| allowed_explanation | 1_to_3_sentences_per_kp |
| max_explanation_length | 120_zh_chars_unless_formula_algorithm_or_implementation_heavy |
| application_condition_required | yes_when_conditions_exist |
| multi_angle_interpretation_required | yes_when_useful |
| source_external_expansion | forbidden_as_required_content |
| source_locator_requirement | internal_traceability_only; do_not_display_kp_id_or_source_location_in_final |
| checkpoint_placement_rule | every_required_kp (subject to Config-Driven Column Rules) |
| through_line_connection_required | yes — every KP's quick_absorption must echo the through-line from `02_analysis/through-line-selection.md` |
| learning_session_layer | forbidden |

## Stage Interface

| export_field | source | destination_stage | purpose |
|---|---|---|---|
| confusion_export | `04_checks/coverage.md` and/or later lesson_loop handoff | lesson_loop / problem_set / feedback_diagnosis | carry unresolved reading problems without exposing workflow fields in the student-facing final artifact |
| fragile_items | pool/knowledge/ + `04_checks/coverage.md` | lesson_loop / problem_set | identify items needing explanation or practice later |
| deferred_extension_items | pool/knowledge/ | lesson_loop or later enrichment | keep extension content out of first-pass core |
| candidate_lesson_upgrade_items | `04_checks/coverage.md` | lesson_loop | identify items likely to require formal lesson expansion |

## Minimum Completion Standard

This file fails if final Markdown structure is planned without `kp_id` bindings, if the KP-level rendering plan lacks `quick_absorption`, question draft, answer key, short answer explanation, answer block group, or forbidden rendering constraints, if checkpoint questions require calculation/proof/code/real operation, if questions can be answered from the quick_absorption statement alone without returning to the source (fails Source-Dependency Self-Check Protocol), if source order changes are not justified, if explanation limits are absent, if the through-line is not connected to every KP's quick_absorption (or gaps not documented in forbidden_rendering), or if the planned artifact reads like a summary, mini-lesson, problem set, formalistic template, exam-prep guide, or timed learning-session plan.
