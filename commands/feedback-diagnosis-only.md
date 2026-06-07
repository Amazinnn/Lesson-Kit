# Command: Feedback Diagnosis Only

Use this command when the user gives exercise feedback and asks for analysis, confirmation questions, or revision planning without requesting final lesson prose.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
RED_LINES.md
FILE_CONTRACT.md
skills/preserve-feedback/SKILL.md
skills/diagnose-weak-points/SKILL.md
skills/learning-evidence-integration/SKILL.md
gates/pre-writing-gate.md
```

## Sequence

1. Preserve feedback in `intermediate/lesson_loop/01_inputs/exercise-feedback-record.md` exactly enough to keep the student's original meaning.
2. Diagnose weak points in `intermediate/lesson_loop/02_analysis/weak-point-diagnosis.md`.
3. Mark high-impact uncertainty in `intermediate/lesson_loop/02_analysis/weak-point-confirmation.md`.
4. If revision planning is requested, write `intermediate/lesson_loop/02_analysis/feedback-to-lesson-map.md` and `intermediate/lesson_loop/03_plans/problem-set-repair-plan.md` where needed.
5. Record a pre-writing/diagnosis check in `intermediate/lesson_loop/04_checks/pre-writing-check.md` if the diagnosis will govern later revision.

## Output File Checklist

```text
[ ] intermediate/lesson_loop/01_inputs/exercise-feedback-record.md
[ ] intermediate/lesson_loop/02_analysis/weak-point-diagnosis.md
[ ] intermediate/lesson_loop/02_analysis/weak-point-confirmation.md if high-impact diagnosis is uncertain
[ ] intermediate/lesson_loop/02_analysis/feedback-to-lesson-map.md if revision planning is requested
[ ] intermediate/lesson_loop/03_plans/problem-set-repair-plan.md if practice repair is needed
```

## Diagnosis Categories

Distinguish terminology confusion, concept boundary failure, missing prerequisite, process-simulation break, condition-recognition failure, representation-conversion failure, neighboring-type confusion, memorized-but-not-usable knowledge, stem misreading, distractor vulnerability, transfer failure, calculation error, carelessness, and broader literacy/ability limitation.

Do not upgrade every feedback item into a lesson knowledge point.
