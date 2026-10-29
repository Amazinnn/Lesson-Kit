## 1. Contract and validation

- [ ] 1.1 Remove the `error_reason is required` check and its docstring clause from `workbench/domain/micro_quiz.py`; keep `answer_key`, `source_evidence`, options, and quiz-type validation unchanged.
- [ ] 1.2 Confirm old `micro_quiz` payloads containing `error_reason` still validate and load because extra payload keys are ignored.
- [ ] 1.3 Update `FILE_CONTRACT.md` to remove the field from the required micro-quiz payload and state that legacy values are ignored.

## 2. UI

- [ ] 2.1 Remove the「判定依据」block from `workbench/server/static/paper-practice.js`; keep「参考答案」and「解析」.
- [ ] 2.2 Update `tests/workbench/paper_practice.test.js` and `tests/workbench/workbench_ui_interactions.test.js` so they no longer expect that section.

## 3. Prompts and preflight

- [ ] 3.1 Remove the two `error_reason` requirements from `workbench/resources/skills/source-bounded-learning-drill/SKILL.md`.
- [ ] 3.2 Remove `error_reason` from `skills/pool-pipeline/references/prompt-t1.md` and `skills/pool-pipeline/references/example.md`.
- [ ] 3.3 Remove the `error_reason` check from `skills/pool-pipeline/scripts/preflight.py`.

## 4. Tests and fixtures

- [ ] 4.1 Update `test_micro_quiz.py`, `test_content_bundle.py`, `test_data_cli.py`, `test_problem_patch.py`, and `test_ingest.py` so keyed items without `error_reason` pass and the old "required" assertions are gone.
- [ ] 4.2 Add a test that a keyed item without `error_reason` is accepted.
- [ ] 4.3 Add a test that an existing payload containing `error_reason` still loads and does not render a「判定依据」section.

## 5. Docs

- [ ] 5.1 Update `docs/DATA_MODEL.md` (remove `error_reason` from the `micro_quiz` field description), `docs/GLOSSARY.md` (micro-quiz and keyless entries), `docs/REQUIREMENTS.md`, and `docs/PRODUCT-MANUAL.md`.
- [ ] 5.2 Register the removal in `docs/ACTION-GRAPH.md` / L3; no new/retired CLI action unless the prompt/preflight change counts as a content-generation rule.

## 6. Verification

- [ ] 6.1 `python -m pytest tests -q`
- [ ] 6.2 `python -m compileall -q lessonkit.py workbench pipeline pool tests`
- [ ] 6.3 `openspec validate --specs --strict`
- [ ] 6.4 `python lessonkit.py guard extract-problems --course dmath --chapter ch06`
- [ ] 6.5 `rg -n "error_reason" workbench/resources/skills skills/pool-pipeline` returns no hits.
