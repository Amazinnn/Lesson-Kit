## Why

`micro_quiz.error_reason` is a second explanation stored inside the objective payload and required whenever an answer key exists. It overlaps the answer key and the full `solution`, adds a mandatory field to every generated objective item, and is shown as a separate「判定依据」block. The owner wants it removed rather than maintained as a parallel explanation.

## What Changes

- Remove `error_reason` from the micro-quiz content contract and its validator requirement. A keyed objective item is valid without it.
- Remove the「判定依据」section from the Paper answer reveal. `answer_key` (参考答案) and `solution` (解析) remain.
- Stop requiring or emitting `error_reason` in the bundled `source-bounded-learning-drill` skill and the `pool-pipeline` prompt/preflight assets.
- Existing `micro_quiz` JSON values that still contain `error_reason` remain readable; the field is ignored by validation and rendering. No physical data migration in this change.
- Update `FILE_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/GLOSSARY.md`, `docs/REQUIREMENTS.md`, `docs/PRODUCT-MANUAL.md`, tests, and fixtures.

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `micro-quiz-content`：payload 不再包含或要求 `error_reason`；带答案键的客观题不带该字段仍合法；旧值被忽略。

## Impact

- Domain/Data validation: `workbench/domain/micro_quiz.py`.
- UI: `workbench/server/static/paper-practice.js` and related tests.
- Agent/pipeline prompts: `workbench/resources/skills/source-bounded-learning-drill/SKILL.md`, `skills/pool-pipeline/references/prompt-t1.md`, `skills/pool-pipeline/references/example.md`, `skills/pool-pipeline/scripts/preflight.py`.
- Docs/contracts: `FILE_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/GLOSSARY.md`, `docs/REQUIREMENTS.md`, `docs/PRODUCT-MANUAL.md`.
- No SQLite column, table, or migration change; `micro_quiz` is a JSON payload.
- Non-goal: physically stripping old `error_reason` keys from existing pool rows. A separate content patch can do that later if wanted.
