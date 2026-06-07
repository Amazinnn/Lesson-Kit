# File Contract

Use this as the current V17 Stage 1 intermediate-file contract. Intermediate files are explicit agent-facing harness artifacts. Do not replace them with private reasoning, final prose, or a claim that the step was considered.

## Stage Folders

V16 completion target is Stage 1 only: `intermediate/first_pass/` and the final `速览` artifact.

Keep the later-stage folders as functional interfaces for future development, but do not treat them as required for V17 Stage 1 completion.

```text
intermediate/first_pass/      source-guided first-pass lesson harness
intermediate/lesson_loop/     lessons, problem sets, answer keys, feedback revision
intermediate/exam_training/   reserved for later exam-stage workflows
```

Each stage uses the same four layers:

```text
01_inputs/      source facts and preserved evidence
02_analysis/    knowledge inventory, shape analysis, weakness, model, and coverage analysis
03_plans/       artifact plans, ordering, rendering, placement, and export decisions
04_checks/      pre-writing and export checks
```

## Required First-Pass Harness Files

For `commands/create-source-guided-first-pass-pack.md`, always require exactly these core harness files before final rendering:

```text
intermediate/first_pass/01_inputs/source-scope.md
intermediate/first_pass/02_analysis/knowledge-points.md
intermediate/first_pass/03_plans/first-pass-structure-plan.md
intermediate/first_pass/04_checks/coverage-check.md
```

These four files are the required harness spine. They must exist as files and must not be represented only in the final Markdown.

Trigger these only when the required harness spine cannot safely express the source structure:

```text
intermediate/first_pass/01_inputs/visual-inventory.md                 when visual-dependent content cannot be audited inside `knowledge-points.md`
intermediate/first_pass/01_inputs/code-algorithm-inventory.md         when code/pseudocode/algorithm traces cannot be audited inside `knowledge-points.md`
intermediate/first_pass/01_inputs/lab-artifact-inventory.md           when lab/system implementation chains cannot be audited inside `knowledge-points.md` and `coverage-check.md`
intermediate/first_pass/01_inputs/example-exercise-inventory.md       when source examples/exercises materially define required first-pass knowledge points
intermediate/first_pass/04_checks/ppt-visual-reading-check.md         when source is PPT/PPTX
intermediate/first_pass/04_checks/visual-dependency-check.md          when visual-dependent content exists
intermediate/first_pass/04_checks/lab-implementation-field-check.md   when lab/system implementation items exist
```

## Required Lesson Files

For textbook/PDF-based lesson work under `intermediate/lesson_loop/`:

```text
01_inputs/source-inventory.md
01_inputs/pdf-reading-log.md                           when PDF/image source is used
01_inputs/thinking-questions-and-examples-inventory.md when present
01_inputs/exercise-inventory.md                        when exercises are used
02_analysis/chapter-knowledge-inventory.md
02_analysis/subject-required-check.md
02_analysis/textbook-body-detail-extraction.md
02_analysis/knowledge-priority-and-dependency.md
02_analysis/thinking-question-example-model-map.md     when present
03_plans/lesson-problem-set-decision.md
03_plans/lesson-integration-plan.md                    when evidence affects the lesson
03_plans/lesson-structure-plan.md
03_plans/lesson-rendering-plan.md
04_checks/pre-writing-check.md
04_checks/lesson-export-check.md
04_checks/format-rendering-check.md
```

When feedback exists, additionally require:

```text
01_inputs/exercise-feedback-record.md
02_analysis/weak-point-diagnosis.md
02_analysis/weak-point-confirmation.md                 when high-impact diagnosis is uncertain
02_analysis/feedback-to-lesson-map.md
03_plans/problem-set-repair-plan.md                    when feedback requires practice or fluency repair
04_checks/feedback-contamination-check.md
```

## Required Problem-Set Files

Under `intermediate/lesson_loop/`:

```text
01_inputs/exercise-inventory.md                        when source exercises exist
01_inputs/full-exercise-bank.md                        when selecting from a full source set
02_analysis/chapter-knowledge-inventory.md
02_analysis/problem-model-space.md
02_analysis/exercise-knowledge-model-map.md            when source exercises exist
02_analysis/type-space-map.md                          when neighboring problem forms matter
03_plans/selected-and-added-problem-list.md
03_plans/exercise-set-format-plan.md
04_checks/problem-set-export-check.md
04_checks/problem-source-consistency-check.md           when source exercises are used
04_checks/exercise-blank-space-check.md                when printable blanks are required
```

## Required Answer-Key Files

Under `intermediate/lesson_loop/`:

```text
03_plans/answer-key-plan.md
03_plans/answer-key-sync-plan.md
04_checks/answer-key-sync-check.md
```

## Layer Rules

- Inputs must preserve source facts and student wording without diagnosis.
- Analysis must state learning type, stable knowledge requirements, knowledge-point candidates, and weak points, not final prose.
- Plans must decide final placement, headings, explanation boundary, rendering, task ordering, exercises, and answer depth.
- Checks must state pass/fail, broken rule, return layer, forbidden repair, and repair action.

## First-Pass Harness Rules

- `knowledge-points.md` is the mandatory full knowledge-point inventory. All later first-pass artifacts must be built around it.
- Textbook/PPT/teacher-required content must be registered in `knowledge-points.md`; it cannot be hidden as deferred content.
- Extension content may be registered as `extension` or `defer`, but it must not become required first-pass mastery unless source evidence requires it.
- The final first-pass artifact is `（科目名） （第X章） （章名） 速览.md`.
- The final artifact may contain short explanations, but each explanation must include application conditions and multi-angle interpretation when applicable.
- Do not create a learning-session plan, time-boxed card, or progress-log layer for first-pass work.

## Required Full Study-Pack Check

For full study-pack export, additionally require under `intermediate/lesson_loop/`:

```text
04_checks/study-pack-delivery-manifest.md
```

The manifest must list the current lesson note, problem set, answer key, package files, and any stale or intentionally omitted companion artifact.
