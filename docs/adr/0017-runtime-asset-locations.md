# ADR 0017: Runtime Asset Locations in Hidden Dot-Directories

## Status

Accepted.

## Context

The project convention is that runtime files live in hidden dot-directories
(`.lessonkit/`, `.claude/`, `.worktrees/`, `.git/`). An earlier draft placed
figures under `intermediate/{course}/...`, which violates that convention:
`intermediate/` is the audited work-product tree, not a runtime home. The same
question applies to AI bridge outputs, previously drafted under
`intermediate/{course}/explain/`.

## Decision

All workbench runtime assets live under the workspace's `.lessonkit/` tree:

```text
.lessonkit/
├── state.yaml                                   # runtime state (tracked)
├── figures/{course}/{chapter}/{owner_id}-fig-{NNN}.png   # tracked
├── explain/{course}/{chapter}/{item_id}.md      # validated bridge results (tracked)
└── jobs/<job-id>/                               # task working files (gitignored)
```

- The pool stores only logical paths (`{course}/{chapter}/{owner_id}-fig-{NNN}.png`);
  each display surface resolves them (workbench static service; exported
  Markdown computes relative paths from the document location).
- `figures/` and `explain/` are tracked learning assets; `jobs/` is transient
  state and is gitignored (`.lessonkit/jobs/`).
- `knowledge_points.figure_paths` and `problems.figure_paths` hold the logical
  paths; problem figures exist because diagrams are often part of the question
  itself (Karnaugh maps, circuit/force diagrams).
- Obsidian rendering of images inside hidden directories is a verified-at-
  implementation acceptance item; if a viewer excludes dot-directories, a
  documented workaround applies and it is not a v1 blocker.

## Consequences

One declared place for all runtime assets, consistent with the project's
hidden-directory convention. Figures and explanations version with the
repository and migrate with it. The cost is one extra resolution step for
Markdown export paths, confined to the content layer.
