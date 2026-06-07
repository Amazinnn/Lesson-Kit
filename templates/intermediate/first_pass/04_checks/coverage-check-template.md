# Coverage Check

## Progressive Update Rule

`coverage-check.md` is a continuously updated audit table, not only a final export gate.

Update it after each required first-pass intermediate file is completed:

```text
source-scope.md completed
→ update source coverage expectations

knowledge-points.md completed
→ update knowledge-point landing and source grounding checks

first-pass-structure-plan.md completed
→ update rendering, question, answer-block, and forbidden-rendering checks

final-first-pass-guide.md drafted
→ run final student-facing output checks
```

The file must remain an audit artifact. Do not turn it into a progress diary. Each update should record pass/fail evidence, return layer, forbidden repair, and repair action.

Use `check_stage` to show when the row was last checked:

```text
after_source_scope
after_knowledge_points
after_structure_plan
final_export
```

## Failure Retention Rule

When a failed matrix row is repaired, update the matrix row to the current status, but keep the failure in the Failure Table.

```text
Matrix rows = current audit status.
Failure Table = triggered failure types, return layers, forbidden repairs, and required repair actions.
```

Do not erase a failure just because it was repaired. Do not create a process-history row for every repair unless the failure created a durable workflow rule or design note.

## Source Coverage Matrix

| check_stage | source_unit_id | source_location | required_status | covered_by_kp_ids | missing | return_to | repair_action |
|---|---|---|---|---|---|---|---|
| after_source_scope / after_knowledge_points / after_structure_plan / final_export | su-001 |  | required / optional / extension |  | yes / no | source-scope.md / knowledge-points.md |  |

## Knowledge Landing Matrix

| check_stage | kp_id | final_section_or_title | source_grounded | learnable_unit | in_final_markdown | has_learning_action | has_minimum_mastery_standard | has_checkpoint_question | pass_fail | return_to |
|---|---|---|---|---|---|---|---|---|---|---|
| after_knowledge_points / after_structure_plan / final_export | course-source-ch03-kp-001 | final student-facing title or section | yes / no | yes / no | yes / no | yes / no | yes / no | yes / no | pass / fail | knowledge-points.md / first-pass-structure-plan.md |

## Failure Table

| failure | return_to | forbidden_repair |
|---|---|---|
| source_unit has no matching knowledge point | `source-scope.md` or `knowledge-points.md` | Adding a vague final paragraph without registering a knowledge point |
| knowledge point is a broad heading rather than a learnable unit | `knowledge-points.md` | Splitting only in final Markdown while leaving the inventory coarse |
| final Markdown contains unregistered knowledge | `knowledge-points.md` and `first-pass-structure-plan.md` | Keeping useful prose that cannot be traced to the inventory |
| textbook/PPT/teacher-required content is marked deferred | `knowledge-points.md` | Rewording it as extension content without source evidence |
| short explanation lacks application conditions where conditions exist | `first-pass-structure-plan.md` and final Markdown | Adding a generic warning not tied to the knowledge point |
| short explanation uses only one interpretive angle where multiple angles are needed | `first-pass-structure-plan.md` and final Markdown | Adding unrelated examples instead of a second valid interpretation angle |
| final artifact introduces a learning-session layer | `first-pass-structure-plan.md` | Renaming sessions as tasks while preserving the same structure |

## Student-Facing Rendering Matrix

| check_stage | final_section_or_kp | hides_kp_id | hides_knowledge_type | hides_writing_view | hides_rendering_intent | hides_template_labels | no_internal_field_names | no_new_umbrella_terms | no_formalism_or_examism_terms | pass_fail | return_to |
|---|---|---|---|---|---|---|---|---|---|---|---|
| final_export | section / kp title | yes / no | yes / no | yes / no | yes / no | yes / no | yes / no | yes / no | yes / no | pass / fail | first-pass-structure-plan.md / final Markdown |

Student-facing output must show knowledge directly, not workflow scaffolding. Fail if the final artifact displays `kp_id`, `knowledge_type`, `writing_view`, `rendering_intent`, internal field names, or labels such as `模板`, `一句话说明`, `掌握检查`, `本题考查`, `题型`, or `解题入口`.

Fail if the final artifact introduces source-absent umbrella terms as student-facing headings or conceptual labels.

Fail if the final artifact drifts into formalism or exam-prep framing. Avoid terms and structures that make Stage 1 look like a template, exam guide, answer routine, scoring rubric, or test-taking strategy rather than a source-reading interface.

Fail if checkpoint questions require calculation, proof, code writing, or real operation. Questions should require returning to the corresponding source section for recognition, condition, boundary, structure, role, or next-step judgment; they should not be answerable from the short statement alone.

This check must cover both explicit wording and structural drift.

Explicit wording failures include labels or phrases such as `解题入口`, `本题考查`, `答题模板`, `得分点`, `高频考点`, `秒杀技巧`, `题型套路`, `考点归纳`, and similar exam-prep or template-language variants.

Structural failures include fixed-column template rendering for every knowledge point, checkpoint questions turning into drill practice, overlong answer explanations that resemble standard answers, sections organized as exam-point summaries, or final prose replacing source reading instead of guiding the student back to the source.

This is a serious gate. Do not pass the final artifact by merely removing banned words while preserving formalistic or exam-prep structure.

## Minimum Completion Standard

This file fails if it only says “covered” without source-unit evidence, knowledge-point IDs, return layer, forbidden repair, and repair action.
