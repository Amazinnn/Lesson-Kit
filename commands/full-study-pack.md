# Command: Full Study Pack

Use this command when the user asks for a complete learning-loop package: lesson note, problem set, and answer key.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
TASK_ROUTER.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
commands/lesson-from-textbook-or-feedback.md
commands/problem-set-from-knowledge.md
commands/answer-key.md
skills/intermediate-contracts/SKILL.md
skills/quality-audit/SKILL.md
gates/pre-writing-gate.md
gates/lesson-export-gate.md
gates/problem-set-export-gate.md
gates/problem-source-consistency-gate.md
gates/answer-key-export-gate.md
gates/format-rendering-gate.md
```

## Sequence

1. Run `commands/lesson-from-textbook-or-feedback.md` through the lesson export gate.
2. Run `commands/problem-set-from-knowledge.md` using the final lesson knowledge architecture and source exercise inventory.
3. Run `commands/answer-key.md` using the final problem set.
4. If any lesson, problem-set, answer-key, formatting, source transcription, Mermaid, or LaTeX change affects companion artifacts, regenerate the affected companion artifacts in the same pass or mark them stale explicitly.
5. Create `intermediate/lesson_loop/04_checks/study-pack-delivery-manifest.md` listing the current lesson note, problem set, answer key, and package files. Do not silently mix old and revised artifacts.
6. Run the format gate and package/export checks.

## Output File Checklist

```text
[ ] lesson note is current and passed lesson/export gates
[ ] problem set is current and passed problem-set/source/format gates
[ ] answer key is current and passed answer-key sync gate
[ ] intermediate/lesson_loop/04_checks/study-pack-delivery-manifest.md
[ ] no stale companion artifact is silently included
```

## Required Principle

The three artifacts have separate jobs:

- lesson note: knowledge structure, definitions, formulas, models, conditions, derivations, processes, boundaries, examples;
- problem set: training mapped to lesson knowledge points;
- answer key: reasoning, key judgments, mapped knowledge, and synchronized solutions.

Do not solve this by writing one giant lesson that contains everything.
