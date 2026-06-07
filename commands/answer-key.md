# Command: Answer Key

Use this command to write or repair an answer key for a finalized problem set.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
skills/answer-key-writing/SKILL.md
skills/diagrams-and-math-rendering/SKILL.md
gates/answer-key-export-gate.md
gates/format-rendering-gate.md
```

## Sequence

1. Read the final problem set and preserve its numbering, wording, order, and tags.
2. Create `intermediate/lesson_loop/03_plans/answer-key-plan.md` to decide explanation depth.
3. Create `intermediate/lesson_loop/03_plans/answer-key-sync-plan.md` mapping every problem to an answer entry.
4. Write the answer key.
5. Run `gates/answer-key-export-gate.md` and record `intermediate/lesson_loop/04_checks/answer-key-sync-check.md`.
6. Run `gates/format-rendering-gate.md` when answer formatting, LaTeX, code, tables, or diagrams are present.

## Output File Checklist

```text
[ ] final problem set exists and is current
[ ] intermediate/lesson_loop/03_plans/answer-key-plan.md
[ ] intermediate/lesson_loop/03_plans/answer-key-sync-plan.md
[ ] answer key file
[ ] intermediate/lesson_loop/04_checks/answer-key-sync-check.md
[ ] intermediate/lesson_loop/04_checks/format-rendering-check.md if formatting gate applies
```

## Rule

The answer key should explain reasoning, key judgments, knowledge calls, and important boundary conditions. It must stay synchronized with the problem set.

If the problem set changes because of formatting, source transcription, Mermaid figure repair, LaTeX cleanup, problem replacement, or blank-space formatting, regenerate or revise the answer key in the same pass unless the user explicitly excludes answer-key work and the stale status is recorded.
