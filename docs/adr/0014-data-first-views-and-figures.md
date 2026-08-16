# ADR 0014: Data-First Views and Knowledge Figures

## Status

Accepted.

## Context

Existing views (knowledge guide, problem set) are rendered Markdown artifacts
in `output/`. The workbench renders from the pool, so presenting both paths
would duplicate logic. Knowledge points with diagrams need a display path that
works in the web workbench and in Obsidian without custom renderers.

## Decision

**Data-first rendering**: the workbench renders views directly from the pool
(queries, not artifacts). The existing Markdown outputs become print/export
artifacts, generated from the same queries on demand. The `[[kp_id]]` wiki-link
format and LaTeX math stay, so exported files remain Obsidian-compatible.

**Figures as files**: knowledge-point figures are files under the workspace
figure area (`intermediate/{course}/figures/...`), referenced by relative
paths in a new `knowledge_points.figure_paths` column and by standard Markdown
image syntax in body text. The web workbench serves them at a deterministic
static path; Obsidian renders the same Markdown images natively. No database
BLOBs, no custom diagram format in v1. Figures are landed by the extraction
pipeline during extraction (source screenshots or re-drawings); figure asset
management tooling is explicitly out of scope for v1.

## Consequences

One rendering path (pool → views) instead of two. Figures are portable across
both reading surfaces and survive pool rebuilds as long as files are
preserved. The cost: figure files are workspace-local and must be backed up
with the workspace, which is already the practice for `intermediate/` and
`pool/*.db`.
