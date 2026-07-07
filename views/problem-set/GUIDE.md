# Problem-Set View

## Positioning

The problem-set view renders a student-facing practice set from the SQLite
problem pool. It is not a problem ingestion command and it does not generate
new problems in v1.

## When To Use

Use this view when:

- The chapter already has KPs in `knowledge_points`.
- The chapter already has durable rows in `problems`.
- The student wants practice, usually from textbook problems by default.

Do not use this view when:

- Problems have not been extracted yet. Run `pipeline/commands/extract-problems.md`.
- The user wants new generated problems. v1 records coverage gaps instead.
- The user wants a knowledge overview. Use the knowledge guide view.

## Defaults

- `source_kind`: `textbook`
- Selection strategy: coverage first, then source order.
- Generated problems: disabled.
- Student-facing problem set: no answers, no `kp_id`, no internal labels.
- Solution file: one entry per selected problem; missing solutions are marked pending.

## Files

```text
views/problem-set/
├── GUIDE.md
├── command.md
├── skills/
├── gates/
└── templates/
```
