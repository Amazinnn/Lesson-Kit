# Command: Printable Exercise Pack

Use this command when the user wants exercise sheets prepared for printing or handwriting.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
skills/printable-blank-space/SKILL.md
skills/problem-set-formatting/SKILL.md
gates/printable-exercise-gate.md
gates/format-rendering-gate.md
```

## Sequence

1. Confirm the problem set or selected problem list.
2. Record blank-space policy in `intermediate/lesson_loop/03_plans/exercise-set-format-plan.md`.
3. Insert blank space after each problem according to the policy.
4. Ensure the answer key mirrors the problem set and replaces writing space with answers.
5. Run `gates/printable-exercise-gate.md` and record `intermediate/lesson_loop/04_checks/exercise-blank-space-check.md`.

## Output File Checklist

```text
[ ] problem set or selected problem list exists
[ ] intermediate/lesson_loop/03_plans/exercise-set-format-plan.md
[ ] printable exercise sheet
[ ] answer key mirrored without blank writing space when answer key is requested or already exists
[ ] intermediate/lesson_loop/04_checks/exercise-blank-space-check.md
```

## Default Blank Space

Unless the user provides a different rule:

- one-part problem: at least 5 blank lines;
- two-part problem: at least 6 blank lines;
- three-part problem: at least 7 blank lines;
- each additional subquestion: add at least 1 blank line;
- long proof, long calculation, drawing, circuit design, or programming problems may require more.
