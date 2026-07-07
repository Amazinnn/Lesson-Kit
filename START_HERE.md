# START HERE

Use this as the runtime road sign for lesson-kit. Choose one governing command
or view, then load only the files named by that path.

## Choose The Path

| User request | Governing path |
|---|---|
| Extract knowledge from a chapter into SQLite | `pipeline/commands/extract-chapter.md` |
| Extract durable problems into SQLite | `pipeline/commands/extract-problems.md` |
| Render a knowledge guide from the pool | `pool/scripts/print-graph.py` plus `docs/design/print-graph-design.md` |
| Render a practice problem set | `views/problem-set/command.md` |

## Current Contract

- One course database: `pool/{course}.db`.
- Chapter filtering uses full prefixes such as `dmath-ch06`.
- Durable problems live in `problems`.
- `questions` is a legacy companion-check table, not the durable problem pool.
- Zip files are external handoff artifacts. Git is the version source of truth.

## Intermediate Directories

Pipeline extraction:

```text
intermediate/{course}/extraction/{chapter}/
intermediate/{course}/problem_extraction/{chapter}/
```

Views:

```text
intermediate/{course}-{chapter}/{view-name}/
```

Required intermediate files are real artifacts. Do not replace them with
private reasoning or final-message claims.
