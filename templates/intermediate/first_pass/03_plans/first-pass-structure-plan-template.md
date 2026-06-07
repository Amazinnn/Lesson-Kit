# First Pass Structure Plan

## Section Structure Plan

| final_section_id | final_section_title | source_unit_basis | kp_ids | purpose | rendering_rule |
|---|---|---|---|---|---|
| fs-001 |  | su-001 | course-source-ch03-kp-001 | source_grounded_first_pass | preserve_source_order / local_dependency_adjustment / implementation_chain |

## KP-Level Rendering Plan

| kp_id | final_section_id | student_visible_title | writing_view_primary | writing_view_secondary | rendering_intent | quick_absorption | question_target | question_form | question_draft | answer_key | answer_explanation | answer_block_group | forbidden_rendering |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| course-source-ch03-kp-001 | fs-001 |  |  |  |  | quick absorption: clean definition/formula statement + one brief interpretation sentence (core insight of the theorem/concept) + one through-line accent sentence choosing a recurring angle; do not write a standalone summary | scene_judgment / concept / condition / boundary / relation | single-choice / true-false / short judgment |  |  | one short sentence | section-end answer block | no kp_id; no knowledge_type; no writing_view; no template labels; no exam-prep framing |

Rules:

- `quick_absorption` is a clean definition/formula statement plus one brief interpretation sentence (core insight of the theorem/concept) plus one through-line accent sentence that chooses a recurring angle from the chapter's knowledge relationship analysis. The interpretation should reveal the operational logic of the concept, not paraphrase the definition. The final lesson may polish it lightly but must not expand it into a mini-lesson or standalone summary.
- `question_draft`, `answer_key`, `answer_explanation`, and `answer_block_group` must be planned here before final rendering.
- `question_form` should use single-choice or true/false as the default, with short judgment only when needed. For scene_judgment questions, use single-choice with 4 options by default.
- Checkpoint questions must not require calculation, proof, code writing, or real operation. Even for algorithm, code, system, or lab items, ask only for recognition, condition, boundary, structure, variable/step role, or next-step judgment.
- Each checkpoint question should require returning to the corresponding source section to answer confidently; it should not be answerable from the short statement alone and should not resemble an exam or textbook exercise.
- `answer_explanation` must stay short, normally one sentence, and must not become a standard-answer routine.
- `forbidden_rendering` must explicitly block internal fields, source-absent umbrella terms, formalistic templates, and exam-prep framing.

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
| checkpoint_placement_rule | every_required_kp |
| learning_session_layer | forbidden |

## Stage Interface

| export_field | source | destination_stage | purpose |
|---|---|---|---|
| confusion_export | intermediate only: coverage-check.md and/or later lesson_loop handoff | lesson_loop / problem_set / feedback_diagnosis | carry unresolved reading problems without exposing workflow fields in the student-facing final artifact |
| fragile_items | intermediate only: knowledge-points.md + coverage-check.md | lesson_loop / problem_set | identify items needing explanation or practice later |
| deferred_extension_items | intermediate only: knowledge-points.md | lesson_loop or later enrichment | keep extension content out of first-pass core |
| candidate_lesson_upgrade_items | intermediate only: coverage-check.md | lesson_loop | identify items likely to require formal lesson expansion |

## Minimum Completion Standard

This file fails if final Markdown structure is planned without `kp_id` bindings, if the KP-level rendering plan lacks `quick_absorption`, question draft, answer key, short answer explanation, answer block group, or forbidden rendering constraints, if checkpoint questions require calculation/proof/code/real operation, if questions can be answered from the short statement alone without returning to the source, if source order changes are not justified, if explanation limits are absent, or if the planned artifact reads like a summary, mini-lesson, problem set, formalistic template, exam-prep guide, or timed learning-session plan.
