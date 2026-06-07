# START HERE

Use this file as the first runtime road sign. Do not wander through the package. Choose the task, then load only the command, skills, gates, and templates named by that task.

## 1. Identify the Task

Use `TASK_ROUTER.md` to choose one governing command:

| User request | Governing command |
|---|---|
| I just got the textbook/materials and need the first pass | `commands/create-source-guided-first-pass-pack.md` |
| Full lesson + problem set + answer key | `commands/full-study-pack.md` |
| Create or revise a lesson from textbook/PDF, exercises, examples, thinking questions, or feedback | `commands/lesson-from-textbook-or-feedback.md` |
| Diagnose feedback without writing final lesson prose | `commands/feedback-diagnosis-only.md` |
| Create a problem set from knowledge architecture / lesson notes / textbook exercises | `commands/problem-set-from-knowledge.md` |
| Write or repair an answer key | `commands/answer-key.md` |
| Create printable exercise sheets with handwriting space | `commands/printable-exercise-pack.md` |
| Update the workflow from session learning | `commands/update-workflow-from-session-learning.md` |

Only one command governs the task. A command may call skills, but skills do not override the command.

## 2. Load the Command, Not the Whole Forest

After choosing the governing command, read its **Required Load List**. The files in that list are mandatory runtime inputs for that command.

Do not search `reference/` during ordinary task execution. `reference/` is for audit, migration, and design review, not for deciding the runtime path.

Do not use `CHANGELOG.md` to choose current files. It is the mandatory version log; historical paths inside it may no longer exist.

## 3. Read the Red Lines

Before doing any work, read `RED_LINES.md`. If any red line conflicts with a local instruction, the red line wins unless the user explicitly changes the workflow.

## 4. Create the Correct Intermediate Stage

A task is complex if it involves a full chapter, PDF/textbook/PPT source, student feedback, existing lesson revision, exercise set, answer key, multiple source files, or a user request to follow the workflow strictly.

For complex tasks, create the stage-specific four-layer workspace immediately:

```text
intermediate/first_pass/01_inputs/      for source-guided first-pass lessons
intermediate/first_pass/02_analysis/
intermediate/first_pass/03_plans/
intermediate/first_pass/04_checks/

intermediate/lesson_loop/01_inputs/     for lessons, problem sets, answer keys, and feedback revision
intermediate/lesson_loop/02_analysis/
intermediate/lesson_loop/03_plans/
intermediate/lesson_loop/04_checks/

intermediate/exam_training/01_inputs/   reserved for later exam-stage workflows
intermediate/exam_training/02_analysis/
intermediate/exam_training/03_plans/
intermediate/exam_training/04_checks/
```

Use `FILE_CONTRACT.md` to decide which files are required.

Required intermediate files are actual deliverables. They cannot be replaced by private reasoning, mental notes, or a final-message claim that the step was considered.

## 5. Do Not Write Final Artifacts Too Early

Before a first-pass lesson, the source scope, knowledge-point inventory, structure plan, and coverage check must exist.

Before lesson prose, the pre-writing files under `intermediate/lesson_loop/` must exist: source scope, knowledge inventory, subject-required check, knowledge priority/dependency, textbook body detail extraction when textbook/PDF is used, feedback record and weak-point diagnosis when feedback exists, lesson/problem-set decision, lesson integration plan when evidence affects the lesson, and lesson structure/rendering plans.

Before a problem set, the knowledge architecture, problem model space, coverage targets, source exercise inventory, selected/added problem list, and formatting plan must exist.

Before an answer key, the final problem set and answer-key sync plan must exist.

## 6. Export Only After Gates Pass

Run the task-specific export gate in `gates/`. A failed gate must name the earlier file or layer to repair. Do not patch the final artifact directly when the error belongs to an analysis or plan file.

## 7. Preserve the Changelog

`CHANGELOG.md` is always retained as the version log. Workflow updates must add a changelog entry instead of treating the file as historical clutter.
