# PR123 content mirror field expansion

The v1 JSON content projection declares validated `figure_paths` references for
knowledge points and problems, plus the complete objective difficulty group
for problems. An explicit content edit may retain a rating only when the same
JSON revision supplies all four non-null dimensions and at least one differs
from the synchronized baseline; other dimension values may stay the same.
Carrying the unchanged vector through a content edit still clears the stale
rating, and an all-null group continues to clear it without rerating. An explicit JSON mirror
revision may update logical references for an already-tracked owner, but it
does not assert byte existence or create, copy, rename, or transport figure
bytes. New image generation and byte attachment remain behind the gated figure
patch channel; its byte-hash checks stay unchanged and repository-wide naming
remains unresolved. Difficulty normalization reuses `data.difficulty.check`;
old schemas are not migrated, and stale clearing touches only represented
fields.

An older v1 mirror baseline can adopt a complete matching projection from the
exact next revision once. Read-only checks remain zero-write, revision spoofing
is rejected, and divergent edits remain conflicts. `schema_version` stays 1.

The field, data-model, architecture, product-manual, glossary, and existing
mirror action contracts are updated. The current `problem-difficulty` and
`knowledge-figures` capabilities now also state the explicit replacement-rating
and reference-only writer boundaries while preserving their prior scenarios.
No CLI action or pool migration is added.

## Focused verification

- `python -m pytest tests/workbench/test_content_mirror.py tests/workbench/test_content_mirror_safety.py tests/workbench/test_content_mirror_schema.py tests/workbench/test_content_mirror_figure_roundtrip.py tests/workbench/test_content_mirror_extended_fields.py tests/workbench/test_figure_mirror.py tests/workbench/test_figure_mirror_index.py tests/workbench/test_difficulty.py tests/workbench/test_mirror_cli.py -q -p no:cacheprovider` — 77 passed.
- `python -m compileall -q workbench/data/content_mirror.py workbench/data/figure_mirror.py tests/workbench/test_content_mirror_extended_fields.py` — passed.
- `openspec validate --all --strict --concurrency 3` — 24 passed, 0 failed.
- `git diff --check` — passed.

Independent full-suite and isolated acceptance passed before this docs-only
specification follow-up. The follow-up is checked with `openspec validate
--all --strict --concurrency 3`, old-scenario equality proof, and `git diff
--check`. OpenSpec archive and final integration remain root-owned.
