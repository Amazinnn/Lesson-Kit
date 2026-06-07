# Command: Lesson From Textbook Or Feedback

Use this command to create or revise a lesson note from textbook/PDF sources, exercises, thinking questions, worked examples, existing lesson notes, and/or student feedback.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
skills/source-and-scope/SKILL.md
skills/intermediate-contracts/SKILL.md
skills/knowledge-inventory/SKILL.md
skills/subject-required-content/SKILL.md
skills/textbook-body-detail-extraction/SKILL.md
skills/learning-evidence-integration/SKILL.md
skills/lesson-structure-planning/SKILL.md
skills/lesson-writing/SKILL.md
skills/scannable-markdown-layout/SKILL.md
gates/pre-writing-gate.md
gates/lesson-export-gate.md
gates/format-rendering-gate.md
```

If PDF/image source is used, also read:

```text
skills/pdf-visual-reading/SKILL.md
gates/pdf-reading-gate.md
```

If feedback exists, also read:

```text
skills/preserve-feedback/SKILL.md
skills/diagnose-weak-points/SKILL.md
```

If the subject is data structures, mathematics, or physics, also read the matching subject skill:

```text
skills/subject-data-structures/SKILL.md
skills/subject-math-physics/SKILL.md
```

If Stage 1 first-pass analysis exists, also load exercise-derived KPs from:

```text
intermediate/first_pass/02_analysis/knowledge-points.md
```

The Exercise-Derived KPs section contains extension knowledge embedded in textbook exercises. Stage 2 should read this to ensure these KPs are covered during lesson writing, even when student feedback is incomplete. If this file does not exist (Stage 1 was not run), the lesson command proceeds without it.

## Entry Conditions

Use this command when the final task is a lesson note or lesson-plan revision and any of these apply:

- source textbook/PDF is provided;
- source exercises, thinking questions, or worked examples are used;
- student exercise feedback is provided;
- an existing lesson note must be improved;
- the user requests strict workflow handling.

Do not use this command for problem-set-only or answer-key-only work except as an upstream source of knowledge architecture.

## Required Sequence

1. Create the four intermediate folders for complex tasks.
2. Lock source scope in `intermediate/lesson_loop/01_inputs/source-inventory.md`.
3. If a PDF/image source is used, create `intermediate/lesson_loop/01_inputs/pdf-reading-log.md` and follow `skills/pdf-visual-reading/SKILL.md`.
4. Preserve exercises, thinking questions, worked examples, and existing lesson structure when present.
5. If feedback exists, create `intermediate/lesson_loop/01_inputs/exercise-feedback-record.md` before any diagnosis.
6. Build `intermediate/lesson_loop/02_analysis/chapter-knowledge-inventory.md` before writing final prose.
7. Run `intermediate/lesson_loop/02_analysis/subject-required-check.md` using the relevant subject skill.
8. Extract textbook body details into `intermediate/lesson_loop/02_analysis/textbook-body-detail-extraction.md` and update or confirm the final knowledge inventory.
9. Build `intermediate/lesson_loop/02_analysis/knowledge-priority-and-dependency.md`.
10. If feedback exists, write `intermediate/lesson_loop/02_analysis/weak-point-diagnosis.md`, `intermediate/lesson_loop/02_analysis/weak-point-confirmation.md` when needed, and `intermediate/lesson_loop/02_analysis/feedback-to-lesson-map.md`.
11. If thinking questions or worked examples exist, write `intermediate/lesson_loop/02_analysis/thinking-question-example-model-map.md`.
12. Decide lesson/problem-set division in `intermediate/lesson_loop/03_plans/lesson-problem-set-decision.md`.
13. Write `intermediate/lesson_loop/03_plans/lesson-integration-plan.md` whenever feedback, body details, thinking questions, examples, or exercise performance affect the lesson.
14. Write `intermediate/lesson_loop/03_plans/lesson-structure-plan.md` and `intermediate/lesson_loop/03_plans/lesson-rendering-plan.md`.
15. Run `gates/pre-writing-gate.md` and record the result in `intermediate/lesson_loop/04_checks/pre-writing-check.md`.
16. Write the lesson note using `skills/lesson-writing/SKILL.md` and `STYLE.md`.
17. Run `gates/lesson-export-gate.md` and `gates/format-rendering-gate.md`; record results in `intermediate/lesson_loop/04_checks/lesson-export-check.md` and `intermediate/lesson_loop/04_checks/format-rendering-check.md`.

## Output File Checklist

Before final lesson prose, check each applicable file:

```text
[ ] intermediate/lesson_loop/01_inputs/source-inventory.md
[ ] intermediate/lesson_loop/01_inputs/pdf-reading-log.md                         if PDF/image source is used
[ ] intermediate/lesson_loop/01_inputs/exercise-feedback-record.md                 if feedback exists
[ ] intermediate/lesson_loop/01_inputs/thinking-questions-and-examples-inventory.md if present
[ ] intermediate/lesson_loop/01_inputs/exercise-inventory.md                       if exercises are used
[ ] intermediate/lesson_loop/02_analysis/chapter-knowledge-inventory.md
[ ] intermediate/lesson_loop/02_analysis/subject-required-check.md
[ ] intermediate/lesson_loop/02_analysis/textbook-body-detail-extraction.md         if textbook/PDF is used
[ ] intermediate/lesson_loop/02_analysis/knowledge-priority-and-dependency.md
[ ] intermediate/lesson_loop/02_analysis/weak-point-diagnosis.md                   if feedback exists
[ ] intermediate/lesson_loop/02_analysis/weak-point-confirmation.md                if high-impact diagnosis is uncertain
[ ] intermediate/lesson_loop/02_analysis/feedback-to-lesson-map.md                 if feedback exists
[ ] intermediate/lesson_loop/02_analysis/thinking-question-example-model-map.md     if thinking questions/examples exist
[ ] intermediate/lesson_loop/03_plans/lesson-problem-set-decision.md
[ ] intermediate/lesson_loop/03_plans/problem-set-repair-plan.md                   if feedback requires practice repair
[ ] intermediate/lesson_loop/03_plans/lesson-integration-plan.md                   if evidence affects the lesson
[ ] intermediate/lesson_loop/03_plans/lesson-structure-plan.md
[ ] intermediate/lesson_loop/03_plans/lesson-rendering-plan.md
[ ] intermediate/lesson_loop/04_checks/pre-writing-check.md
```

Before export:

```text
[ ] intermediate/lesson_loop/04_checks/feedback-contamination-check.md              if feedback exists
[ ] intermediate/lesson_loop/04_checks/lesson-export-check.md
[ ] intermediate/lesson_loop/04_checks/format-rendering-check.md
```

## Blockers

Stop before final lesson prose if any required analysis or plan file is missing or only filled as a placeholder. Stop before export if any gate fails.

If a check fails, repair the earliest broken layer: source record, analysis, plan, then final prose. Do not satisfy a failed analysis/plan gate by only polishing final prose.
