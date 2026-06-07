# Gate: First-Pass Lesson Quality

Use this gate before exporting a source-guided first-pass lesson.

| Failure | Return to | Forbidden repair |
|---|---|---|
| Final artifact reads like a chapter summary, mini-lesson, formal lesson note, problem set, formalistic template, exam-prep guide, answer routine, scoring rubric, drill sheet, or learning-session plan | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` and `04_checks/coverage-check.md` | Deleting a few words while leaving the same summary/template/exam-prep structure intact |
| Final artifact displays `kp_id`, source locations, `knowledge_type`, `writing_view`, `rendering_intent`, template labels, or other internal fields | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` and `04_checks/coverage-check.md` | Hiding only one field while leaving other workflow scaffolding visible |
| Final artifact contains old workflow scaffold modules such as 使用说明, 来源与范围, 本章学习形态, 源材料结构, 知识点检查问题, 首读后回忆单, or 后续阶段接口 | `templates/first-pass/first-pass-lesson-template.md`, `STYLE.md`, and `first-pass-structure-plan.md` | Renaming scaffold sections with more natural titles while preserving the same structure |
| `knowledge-points.md` is missing or not the full inventory | `intermediate/first_pass/02_analysis/knowledge-points.md` | Claiming coverage in final prose without registering knowledge points |
| Knowledge points lack source locations | `intermediate/first_pass/02_analysis/knowledge-points.md` | Adding vague “source: textbook” labels |
| Knowledge points are broad headings rather than learnable units | `intermediate/first_pass/02_analysis/knowledge-points.md` | Splitting only the final Markdown while leaving the inventory coarse |
| Knowledge points lack `knowledge_type`, `source_form`, learning actions, minimum mastery standards, final Markdown locations, or checkpoint questions | `intermediate/first_pass/02_analysis/knowledge-points.md` | Adding generic “read this section” prompts |
| Source coverage matrix, knowledge landing matrix, or student-facing rendering matrix is missing | `intermediate/first_pass/04_checks/coverage-check.md` | Adding an informal note that everything was checked |
| Textbook/PPT/teacher-required content is marked deferred | `intermediate/first_pass/02_analysis/knowledge-points.md` | Rewording required content as extension content without source evidence |
| Section order does not follow source and no allowed reorder is recorded | `intermediate/first_pass/01_inputs/source-scope.md` and `03_plans/first-pass-structure-plan.md` | Reordering only final headings after item generation |
| Short explanation exceeds the allowed boundary or replaces source reading | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` | Shortening sentences without restoring source-reading function |
| Checkpoint questions require calculation, proof, code writing, real operation, or can be answered from the short statement alone without returning to the source | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` and `04_checks/coverage-check.md` | Making the question look simpler while preserving exercise-like behavior |
| Application conditions are missing where conditions, prerequisites, inputs, boundaries, or invalid cases exist | `intermediate/first_pass/02_analysis/knowledge-points.md` and final artifact | Adding a generic “pay attention to conditions” warning |
| Multi-angle interpretation is missing where the item needs more than one angle | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` and final artifact | Adding unrelated examples instead of a second valid interpretation angle |
| Later-stage interface fields are missing from intermediate files when needed for future development | `intermediate/first_pass/03_plans/first-pass-structure-plan.md` | Putting `confusion_export`, `fragile_items`, or other interface fields into the student-facing final artifact |

Pass only when the artifact clearly functions as a source-grounded first-pass lesson generated through the required harness spine.
