# Proposal: Versioned figure assets

## Why

The authored-content repository already makes governed knowledge points, formal
problems, and relations reviewable through Git, but figure bytes are deliberately
outside the JSON projection.  That leaves an important part of authored problem
content outside the repository even though course figure sets are small enough to
version directly and image edits benefit from ordinary branches, pull requests,
and rollback.

The current runtime also mixes tracked figure assets into `.lessonkit/`, beside
provider jobs and other runtime state.  A full directory migration would disrupt
active local Agent work, so this change introduces a repository asset boundary
without requiring an immediate workspace rewrite.

## What changes

- The authored-content repository gains a top-level `figures/<course>/...` area
  containing the exact bytes referenced by the pool's `figure_paths` fields.
- `lesson-kit mirror <workspace> figures` gains explicit `check`, `push`, and
  `pull` directions.  It operates only on the supplied local checkout and never
  invokes Git network commands.
- After legacy identity checks pass, workspace figure lookup for mirror
  operations prefers the future top-level `figures/` asset area and falls back
  to the existing `.lessonkit/figures/` runtime area.
- Pull writes both the top-level asset copy and the legacy runtime copy during
  the transition, so the existing workbench continues rendering without a flag
  day.
- Figure bytes stay outside SQLite and outside JSON entity envelopes.  Pool
  logical references remain the authority for which assets belong to authored
  content.
- This change does not prune repository files, rename existing hash-based
  logical paths, or move the workbench/ingest runtime root.  Stable owner-scoped
  naming and final runtime migration may follow after current bulk image repair
  work finishes.

## Non-goals

- Whole-workspace Git mirroring.
- Git clone/pull/commit/push inside Lesson Kit.
- Repository-only creation of a problem or knowledge point.
- Automatic conflict winner selection for differing binary files.
- Storing image bytes in SQLite or embedding them in JSON/base64 documents.
