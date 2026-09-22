# START HERE

Use this as the runtime road sign for lesson-kit. Choose one governing command
or view, then load only the files named by that path.

## Choose The Path

| User request | Governing path |
|---|---|
| Extract knowledge from a chapter into SQLite | `pipeline/commands/extract-chapter.md` |
| Extract durable problems into SQLite | `pipeline/commands/extract-problems.md` |
| Import governed knowledge points, problems, cards, or figures | `lesson-kit ingest` or the Agent `content-bundle` action |
| Render a knowledge guide from the pool | `pool/scripts/print-graph.py` plus `docs/design/print-graph-design.md` |
| Render a practice problem set | `views/problem-set/command.md` |

## Current Contract

- One course database: `pool/{course}.db`.
- Chapter filtering uses full prefixes such as `dmath-ch06`.
- Durable problems live in `problems`.
- The candidate store was physically removed (2026-08-30): Agent-created content
  has exactly one channel — one governed `content-bundle` manifest (knowledge
  points, problems, micro quizzes, flash cards, required figures) with one
  prevalidation, one backup, one `batch-NNN`, and whole-batch rollback. Any
  invalid item or missing image writes nothing; nothing is silently trusted from
  conversation text. A valid append-only action runs on its own (no keyword
  intent); updates, deletes, rollback, and difficulty still need an explicit
  instruction.
- `questions` is a legacy companion-check table, not the durable problem pool.
- Zip files are external handoff artifacts. Git is the version source of truth.

## Intermediate Directories

Pipeline extraction:

```text
intermediate/{course}/extraction/{chapter}/
intermediate/{course}/problem_extraction/{chapter}/
intermediate/{course}/problem_generation/{chapter}/
```

Views:

```text
intermediate/{course}-{chapter}/{view-name}/
```

Required intermediate files are real artifacts. Do not replace them with
private reasoning or final-message claims.
