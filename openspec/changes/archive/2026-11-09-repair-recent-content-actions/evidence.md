# 2026-11-09 repair evidence

Baseline: `8b1c89c7413b184a84da6fd450e2aa163246f8e5` on local main. Tests use temporary fixture courses. This task did not run real-course mutation, service restart, package-install or runtime-cutover commands.

## Reproduction and repair

| Failure | Regression coverage | Repair |
|---|---|---|
| Corrected bundle repeats a successful auto-ID KP | `test_auto_id_corrected_retry_reuses_unchanged_knowledge_point`; explicit-ID and ambiguous-match cases | Exact same-chapter authored-field reuse, with existing-entity error and zero new KP count; no guessed request identity |
| New KP in another chapter is rejected as a dependency | Both chapter directions in one bundle, cross-chapter failed KP, late batch failure | Stage KPs across connected chapters before dependencies; per-item savepoints and component provenance rollback |
| Non-object micro-quiz crashes valid neighbours | `test_non_object_items_do_not_block_valid_neighbours` | Filter already accepted items rather than re-reading rejected raw input |
| Method association retains stale objective difficulty | New association clears all six fields; repeated association preserves a new rating | Reuse the common problem update writer |
| Temporary legacy-action failure becomes terminal invalidity | Errors in preview/update, real publication-path FileNotFoundError, missing target, reopen at most once | Catch only known input errors, distinguish `UnknownPracticeSet`, propagate operational errors without consuming the artifact |
| Final SQLite commit failure leaves new files | Injected Connection commit failure with new and pre-existing shared figures | Outer new-file list cleaned after rollback, original shared files preserved |
| Interrupted figure copy leaves a corrupt destination | Partial bytes followed by OSError, then corrected retry | Register destination ownership before copying; per-unit failure removes partial output |
| Interrupted initial snapshot write leaves a partial manifest | `test_interrupted_snapshot_write_is_cleaned_before_independent_chapter_continues` (failed with two residual files before repair) | Register snapshot ownership before its first write; roll back only the connected component and continue independent chapters |
| Partial errors disappear before reaching the conversation | Actual Bridge regressions for mixed and zero successful units; Node cases for zero, one and two batches | Preserve receipt fields through both allowlists, report actual activity/context outcomes, and reuse existing result cards for partial reasons |
| Agent is told the old whole-manifest atomic rule | `test_agent_contracts.py` and conversation prompt checks | Synchronize map and detailed content contract with independent-unit semantics |

The five original defects were reproduced with failing regression tests before their fixes. The three additional reviewer findings were likewise added as failing regressions before repair. Related suites now pass: **100 tests**. The final combined six-file Python run passed **189 tests in 37.82s**, including the actual Bridge partial-result regressions.

## Contract reconciliation

- Updated only the affected current knowledge-content-operations and direct-project-actions requirement blocks and their repair deltas.
- Synchronized FILE_CONTRACT, DATA_MODEL, ARCHITECTURE, PRODUCT-MANUAL, ACTION-GRAPH, status handoff, Agent map and on-demand content contract. No new endpoint, CLI syntax, schema field, action level or glossary concept was introduced.
- Restored 19 omitted current scenarios across five active planning delta files. The settings delta retains the confirmed course-preference writer; the Attempt delta retains structured grading and unmigrated-pool behavior alongside its intended Paper import behavior. Other planned increments remain active rather than being declared implemented.
- Independent review confirmed all original scenario titles remain in those five deltas and all 19 missing scenarios were restored; the intended Paper import and evaluation increments remain present.
- The sixth validation failure was an entirely empty residual `complete-live-display-preferences/specs/practice-set-export` directory; its actual change was already archived. Removed the empty directories, without adding a fake skip_specs declaration or modifying the archive.

## Verification

- `openspec validate --all --strict --json`: **42/42** (26 specs, 16 changes).
- `python -m compileall -q lessonkit.py workbench pipeline pool tests`: exit 0.
- `python lessonkit.py guard extract-problems --course dmath --chapter ch06`: PASS.
- `node --test <all tests/workbench/*.test.js>`: **299 passed**, zero failures/skips.
- `git diff --check`: exit 0.
- Independent reviewer reproduced the additional three failure boundaries, then re-ran the repaired focused suites: **99 passed in 12.15s**, no remaining P1/P2 found in the reviewed implementation.
- Independent full repository run on the final frozen source: `PYTHONUTF8=1 python -m pytest tests -q --tb=short`: **1599 passed in 476.89s**, exit 0. Final additional context verification: **89 passed in 22.89s**. Final independent diff review found no remaining P1/P2.
- Full-run log: `C:/Users/yanwei/AppData/Local/Temp/lesson-kit-independent-review-accepted-freeze-full-20261109.log`; context log: `C:/Users/yanwei/AppData/Local/Temp/lesson-kit-independent-review-final-context-20261109.log`. Only the frozen-source completed run is counted; earlier interrupted runs are excluded.

No live model, browser interaction, installed-runtime cutover or real-course migration acceptance is claimed. This change remains available as the handoff for any separate release work.
