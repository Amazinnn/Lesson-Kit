# Tasks

## 1. Binary mirror core

- [x] 1.1 Add a figure mirror data module that reads only pool-referenced logical paths.
- [x] 1.2 Validate course/path/extension boundaries before writes.
- [x] 1.3 Implement read-only check plus explicit push and pull directions.
- [x] 1.4 Prefer top-level workspace figures and retain `.lessonkit/figures` fallback.
- [x] 1.5 Pull into both workspace locations for current renderer compatibility.
- [x] 1.6 Keep deletion/pruning and Git network transport out of the mirror.
- [x] 1.7 Generate a searchable per-course owner index for hash-named legacy assets.

## 2. CLI

- [x] 2.1 Add `lesson-kit mirror <workspace> figures --repo ... --direction check|push|pull`.
- [x] 2.2 Support `--dry-run` for directional file plans.
- [x] 2.3 Preserve existing JSON mirror command behavior and exit semantics.

## 3. Regression coverage

- [x] 3.1 Cover legacy-only push.
- [x] 3.2 Cover top-level workspace preference.
- [x] 3.3 Cover pull dual-write compatibility.
- [x] 3.4 Cover check/dry-run read-only behavior.
- [x] 3.5 Cover all-source prevalidation and path traversal/foreign-course refusal.
- [x] 3.6 Cover a logical figure shared by multiple authored owners.
- [x] 3.7 Cover canonical owner-index generation and stale-index reporting.
- [x] 3.8 Refuse differing existing copies at a legacy 64-hex content identity and refuse a repo-only pull without a workspace baseline.
- [x] 3.9 Cover workspace/repository root redirection with Windows junctions or symlinks.
- [x] 3.10 Preflight the derived index path before copies, including an empty reference list.
- [x] 3.11 Reject missing/non-file or unmanaged pool databases while preserving legacy owner tables without `figure_paths` columns.

## 4. Contract and handoff

- [x] 4.1 Define the repository `figures/<course>/...` binary asset area.
- [x] 4.2 Keep figure bytes outside JSON envelopes and SQLite.
- [x] 4.3 Document the temporary dual workspace layout while current bulk repair runs.
- [x] 4.4 Run exact-head repository CI and resolve any contract/test failures (6d8150e; GitHub Actions 38318316270, Python 3.11/3.12 passed).
- [x] 4.5 Open a reviewable PR without merging it while the owner is occupied with local repair work.
- [x] 4.6 Reconcile the glossary, capability delta, file contract, DATA_MODEL, architecture, manual, and action graph after the PR113 audit.
- [x] 4.7 Record the bounded fix and its per-file atomicity limit in the dated handoff.

## Follow-up, intentionally out of scope

- Switch workbench serving/ingest/rollback from `.lessonkit/figures` to the visible top-level `figures/` area after active repair work finishes.
- Migrate legacy hash-based logical names to stable owner-scoped names such as `<course>/<chapter>/<owner-id>/fig-001.png` where useful.
- Decide explicit add/remove semantics for figures not already referenced by the pool.
