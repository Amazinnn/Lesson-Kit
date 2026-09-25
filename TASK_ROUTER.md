# Task Router

Choose one governing path. Do not let older V17 task names or historical zip
packages govern current lesson-kit work.

| Task signal from user | Governing path | First required artifact |
|---|---|---|
| "extract this chapter", "build the KP pool" | `pipeline/commands/extract-chapter.md` | `pool-insert-manifest.json` |
| "extract the exercises/problems", "build the problem pool" | `pipeline/commands/extract-problems.md` | `full-problem-bank.md` |
| "import these exercises", "add knowledge points or figures", "generate checks", "add flash cards/micro quizzes" | Agent content action (`content-bundle`; legacy `flash-card-patch` / `micro-quiz-patch` still accepted) | complete governed manifest, staged under `.lessonkit/jobs/conv-NNN/` |
| "print a paper / practice set for chapter X", "give me my wrong problems" | `lesson-kit pull <workspace> … --plan/--print` | a composed practice manifest (or the two rendered Markdown files) |
| "rate these problems", "rerate difficulty" | `lesson-kit difficulty <workspace> check` then `apply` | complete four-dimension rating manifest |
| "record my handwritten answer", "grade this photo of my work", "fix the rating you just recorded" | `lesson-kit attempts <workspace> check\|apply\|correct --input <file\|->` | attempt manifest (`request_id` + `items[]`), plus `sources list` for the answer-image directories |
| "show me the knowledge guide", "print the chapter guide" | `pool/scripts/print-graph.py` | existing `knowledge_points` rows |
| "make a problem set", "practice problems" | `views/problem-set/command.md` | existing `problems` rows |

## Runtime First

If `.lessonkit/state.yaml` exists, read it before routing work. Do not infer
the current workflow state only from directory contents or chat history.

```bash
python lessonkit.py status
python lessonkit.py resume
```

When a command's required artifacts are expected to be complete, run its guard:

```bash
python lessonkit.py guard extract-chapter --course <course> --chapter <chapter> --apply
python lessonkit.py guard extract-problems --course <course> --chapter <chapter> --apply
python lessonkit.py guard problem-set --course <course> --chapter <chapter> --apply
```

For local extraction work with an available SQLite pool, prefer the stronger
form:

```bash
python lessonkit.py guard extract-chapter --course <course> --chapter <chapter> --db pool/<course>.db --apply
python lessonkit.py guard extract-problems --course <course> --chapter <chapter> --db pool/<course>.db --apply
```

Do not pass `--db` to `problem-set`; the problem-set guard checks view
artifacts and rendered outputs.

`phase: blocked` means repair the reported artifact or check file before
continuing. `phase: complete` means use `next_action` to choose the next
workflow step.

## Routing Rules

- Run KP extraction before problem extraction.
- Run problem extraction before problem-set rendering.
- Keep frozen sourced-problem extraction separate from Agent Check ingest.
- Problem-set rendering never generates content. Agent-generated flash cards
  and micro quizzes enter the durable pool directly only after their governed
  manifest passes the Check gate; no candidate state exists.
- The student-facing problem set hides KP IDs and solutions.
- The solution file mirrors problem numbering and marks missing solution text as `待补`.
