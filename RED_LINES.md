# Source-Guided First-Pass Red Lines

1. A first-pass lesson must not replace textbook/source reading. It must send the student back to the source.
2. Do not generate chapter summaries, mini-lessons, full explanations, or long answer explanations inside the first-pass lesson.
3. Every knowledge point must have a source location, a reading task, and a concrete checkpoint question.
4. Every required knowledge point must preserve traceability through `knowledge-points.md` and `first-pass-structure-plan.md`; do not display `kp_id` in the student-facing final artifact.
5. Do not introduce a learning-session layer, time-boxed card, progress log, or timed route into the first-pass stage.
6. The required harness spine is `source-scope.md`, `knowledge-points.md`, `first-pass-structure-plan.md`, and `coverage-check.md`. Do not treat any of these as optional.

7. The final student-facing artifact ('速览') must not contain workflow terminology. '首读', '回看', '先确认', '不要急着', and similar workflow-process language are prohibited in the final artifact. The artifact must read as a standalone knowledge organization indistinguishable from a well-designed study guide.

## Intermediate-File Red Lines

1. Intermediate files are contracts, not progress logs.
2. `01_inputs` records evidence and sources; it must not diagnose.
3. `02_analysis` analyzes knowledge, source shape, learning items, and weaknesses; it must not write final prose.
4. `03_plans` decides placement, order, rendering, explanation boundary, and export interface.
5. `04_checks` must record pass/fail, broken rule, return layer, forbidden repair, and repair action.

## Writing Rules

1. Use `$...$` for inline LaTeX and `$$...$$` only for long, central, or multi-step formulas.
2. Do not use `\(...\)` or `\[...\]` in Markdown artifacts.
3. Use one `#` title. For ordinary chapter notes and first-pass lessons use `###` and `####`; avoid routine `##` and avoid headings deeper than `####`.
4. Use Mermaid, tables, and diagrams only when they clarify structure, comparison, process, dependency, state transition, timeline, or workflow.
5. Keep visuals sparse. They should support the text, not dominate it.

## Anti-Formalism and Anti-Examism Red Line

First-pass lessons must not drift into formalistic templates or exam-prep framing.

Do not use explicit exam/template wording such as `解题入口`, `本题考查`, `答题模板`, `得分点`, `高频考点`, `秒杀技巧`, `题型套路`, `考点归纳`, or similar variants.

Do not show internal fields or labels such as `kp_id`, source location, `knowledge_type`, `writing_view`, `rendering_intent`, `question_target`, answer-block metadata, template labels, or other workflow scaffolding in the student-facing final artifact.

Do not ask for calculation, proof, code writing, or real operation in Stage 1 checkpoint questions. Checkpoint questions should send the student back to the source for recognition, condition, boundary, structure, role, or next-step judgment.

Do not preserve the same drift structurally after removing the words. Forbidden structures include fixed-column template rendering for every knowledge point, checkpoint questions becoming drill practice, overlong answer explanations that resemble standard answers, sections organized as exam-point summaries, or final prose replacing source reading instead of guiding the student back to the source.
