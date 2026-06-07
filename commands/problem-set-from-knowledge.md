# Command: Problem Set From Knowledge

Use this command to create a separate problem set mapped to lesson knowledge points.

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
skills/problem-model-space/SKILL.md
skills/problem-set-selection/SKILL.md
skills/problem-set-formatting/SKILL.md
skills/diagrams-and-math-rendering/SKILL.md
gates/problem-set-export-gate.md
gates/problem-source-consistency-gate.md
gates/format-rendering-gate.md
```

If printable blank space is required, also read:

```text
skills/printable-blank-space/SKILL.md
gates/printable-exercise-gate.md
```

## Sequence

1. Read or create `intermediate/lesson_loop/02_analysis/chapter-knowledge-inventory.md` and the knowledge architecture needed by the lesson/problem-set scope.
2. Build `intermediate/lesson_loop/02_analysis/problem-model-space.md`: dimensions, condition axes, neighboring variants, and transfer changes.
3. If source exercises exist, create `intermediate/lesson_loop/01_inputs/exercise-inventory.md` and `intermediate/lesson_loop/01_inputs/full-exercise-bank.md` before selecting.
4. Solve or answer-model source/candidate exercises in `intermediate/lesson_loop/02_analysis/exercise-knowledge-model-map.md` before filtering when selection quality, answer synchronization, or source fidelity depends on problem understanding.
5. Build `intermediate/lesson_loop/02_analysis/type-space-map.md` when neighboring problem forms matter.
6. Group homogeneous problems and remove redundant duplicates only after knowledge/model/condition/training-target comparison.
7. Decide coverage and additions in `intermediate/lesson_loop/03_plans/selected-and-added-problem-list.md`.
8. Record formatting in `intermediate/lesson_loop/03_plans/exercise-set-format-plan.md`.
9. Write the problem set with answers excluded.
10. Run `gates/problem-set-export-gate.md`, `gates/problem-source-consistency-gate.md` when sources are used, and `gates/format-rendering-gate.md`.

## Output File Checklist

```text
[ ] intermediate/lesson_loop/02_analysis/chapter-knowledge-inventory.md
[ ] intermediate/lesson_loop/02_analysis/problem-model-space.md
[ ] intermediate/lesson_loop/01_inputs/exercise-inventory.md              if source exercises exist
[ ] intermediate/lesson_loop/01_inputs/full-exercise-bank.md              if selecting from a full source set
[ ] intermediate/lesson_loop/02_analysis/exercise-knowledge-model-map.md  if source/candidate exercises affect selection
[ ] intermediate/lesson_loop/02_analysis/type-space-map.md                if neighboring variants matter
[ ] intermediate/lesson_loop/03_plans/selected-and-added-problem-list.md
[ ] intermediate/lesson_loop/03_plans/exercise-set-format-plan.md
[ ] intermediate/lesson_loop/04_checks/problem-set-export-check.md
[ ] intermediate/lesson_loop/04_checks/problem-source-consistency-check.md if source exercises are used
[ ] intermediate/lesson_loop/04_checks/format-rendering-check.md
[ ] intermediate/lesson_loop/04_checks/exercise-blank-space-check.md       if printable blanks are required
```

## Rule

Do not start by picking questions. Build the training space first.

Do not filter candidate exercises before they are sufficiently solved or answer-modeled to compare knowledge target, condition signature, technique, representation, boundary, error lure, and training value.
