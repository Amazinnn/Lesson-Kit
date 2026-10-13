# PR123 content mirror field expansion

The v1 JSON content projection now declares validated `figure_paths` references
for knowledge points and problems, plus the complete objective difficulty group
for problems. Reference validation reuses the figure mirror's existing logical
path rules; figure bytes remain in the separate directional mirror. Difficulty
normalization reuses `data.difficulty.check`; old schemas are not migrated, and
content edits clear only difficulty columns present in the pool projection.

An older v1 mirror baseline can adopt a complete matching projection from the
exact next revision once. Read-only checks remain zero-write, revision spoofing
is rejected, and divergent edits remain conflicts. `schema_version` stays 1.

The field, data-model, architecture, product-manual, glossary, and existing
mirror action contracts are updated. No CLI action or pool migration is added.

## Focused verification

- `python -m pytest tests/workbench/test_content_mirror.py tests/workbench/test_content_mirror_safety.py tests/workbench/test_content_mirror_schema.py tests/workbench/test_content_mirror_figure_roundtrip.py tests/workbench/test_content_mirror_extended_fields.py tests/workbench/test_figure_mirror.py tests/workbench/test_figure_mirror_index.py tests/workbench/test_difficulty.py tests/workbench/test_mirror_cli.py -q -p no:cacheprovider` — 77 passed.
- `python -m compileall -q workbench/data/content_mirror.py workbench/data/figure_mirror.py tests/workbench/test_content_mirror_extended_fields.py` — passed.
- `openspec validate --all --strict --concurrency 3` — 24 passed, 0 failed.
- `git diff --check` — passed.

Full-suite, isolated-environment, and release acceptance remain with the
independent final gate.
