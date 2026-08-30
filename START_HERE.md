# START HERE

Use this as the runtime road sign for lesson-kit. Choose one governing command
or view, then load only the files named by that path.

## Choose The Path

| User request | Governing path |
|---|---|
| Extract knowledge from a chapter into SQLite | `pipeline/commands/extract-chapter.md` |
| Extract durable problems into SQLite | `pipeline/commands/extract-problems.md` |
| Generate governed flash cards or micro quizzes | `wb ingest` or an explicit Agent `check_ingest` action |
| Inspect or maintain legacy candidate records | `wb data <workspace> ... candidate` |
| Render a knowledge guide from the pool | `pool/scripts/print-graph.py` plus `docs/design/print-graph-design.md` |
| Render a practice problem set | `views/problem-set/command.md` |

## Current Contract

- One course database: `pool/{course}.db`.
- Chapter filtering uses full prefixes such as `dmath-ch06`.
- Durable problems live in `problems`.
- The old `candidate_problems` table remains for compatibility and maintenance,
  but active practice reads formal `problems` only.
- Agent-created flash cards and micro quizzes enter through the Check ingest
  contract: deterministic gate, batch-recorded transaction, and whole-batch
  rollback. They are not silently trusted from conversation text.
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
