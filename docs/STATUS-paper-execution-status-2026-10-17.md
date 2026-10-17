# Paper execution status implementation handoff — 2026-10-17

## State

Implementation is in `D:\Projects\Academic Workflow\lesson-kit\.worktrees\paper-execution-status`, branch `fix/paper-execution-status`. The production and test implementation is committed through `a7a57c28d5bf377c0233545c2e3f94afb1ede2b4`; the approved contract and handoff documentation is delivered as a separate docs-only follow-up. No real workspace or pool database was read or changed.

The read/action status in `data.paper_progress` compares the saved Paper's ordered problem identities with its active or parked execution, then checks item availability, structure generation, problem content revisions, and the current manifest validation. Saved reads attach execution progress only when this status is available. Active-practice reads use the same result. Start and park revalidate it before changing state.

When another saved Paper is active and cannot be parked, the target record carries a separate `start_block_reason`; the target's own continuation and progress remain intact. The start action rejects before changing either execution. List and active-practice UI use backend readiness. A rejected list start fetches the record again and updates the count, progress, start label, readiness and reason in place, preserving unsaved card edits. Old execution counts and unavailable IDs are shown separately in collapsed details. Valid container management remains available independently from continuation.

No state restoration, identity remapping, evidence deletion, schema migration, dependency, or frozen pipeline/pool/lessonkit contract was added. The existing glossary entry for Paper Execution Progress was sufficient; no new glossary noun was introduced.

## Implementation commits

- `3beee708` — shared Data continuation status, saved reads and active/parked checks, initial focused tests.
- `bb429551282542e2d9969255bce7588420291b0c` — stale list-action refresh updates current count/progress and button text without rerendering.
- `a7a57c28d5bf377c0233545c2e3f94afb1ede2b4` — different active Paper blocker, active manifest validation, and the persisted `card` item-type check.

## Verification evidence

The original count mismatch reproduction failed because a 3-item execution's `1/3` progress was attached to the current 2-item Paper. The corrected implementation reports no current Paper progress, keeps the old execution count separately, and rejects continuation without changing the execution or learning evidence.

The focused red checks also exposed the stale card label (`继续练习` remained after the refreshed record returned 22 items and no progress), a target Paper incorrectly marked startable while another invalid Paper was active, and a persisted `card` item incorrectly listed as unavailable. Each now passes with the corresponding fix.

Final focused commands on the committed implementation:

```text
python -m pytest tests/workbench/test_paper_progress.py tests/workbench/test_saved_practice_sets.py -q
28 passed

python -m pytest tests/workbench/test_ui_routes.py::UiRouteTests::test_mismatched_execution_keeps_paper_management_and_folds_legacy_ids tests/workbench/test_ui_routes.py::UiRouteTests::test_other_paper_readiness_reports_unparkable_active_paper tests/workbench/test_ui_routes.py::UiRouteTests::test_active_practice_api_includes_saved_manifest_validation_readiness -q
3 passed

node --test --test-name-pattern="broken legacy progress|rejected stale paper start|active paper readiness" tests/workbench/workbench_ui_interactions.test.js
4 passed

git diff --check
passed
```

## Independent final acceptance

Final production/tests are frozen at `a7a57c28d5bf377c0233545c2e3f94afb1ede2b4`; subsequent commits contain documentation only. Final fresh Python suite: **1049 passed in 206.26 seconds**, exit 0 with `PYTHONUTF8=1`. All 10 official Node test files: **205 passed**. Required compileall, extraction guard, strict live specifications (19/19), strict all OpenSpec before archive (27/27), and diff checks passed.

Independent local Chromium and API acceptance passed 17 assertion groups, including all three defects found during review: stale-card count/progress/button-label refresh, another active Paper blocking the target start without attaching its progress, and invalid active manifests disabling practice resume. Counts 70/19 versus 22, same-count order mismatch, folded unavailable IDs, revision/generation conflicts, valid continuation and independent export/download/rename/delete were exercised. Full table and manifest snapshots confirmed no changes on reads or rejected actions; drafts and learning evidence were preserved. No real course data was used or changed.

Evidence: `C:/Users/yanwei/AppData/Local/Temp/lesson-kit-paper-final-09979438bc0f42d2b53024b76b0014fb/`, including `result.json`, numbered snapshots/screenshots, driver script and `cleanup.json`. The isolated server on port 53768 and its browser were stopped; harness exit code 0.

The implementation and initial independent review used gpt-6-luna max. After its quota was exhausted, a fresh gpt-6.1-sol agent completed independent final review and verification; the controller reviewed the result. This is ordinary independent acceptance, not a calibrated constrained-reviewer ACCEPT gate, because enforced read-only isolation was unavailable.

Earlier planning documents written through a PowerShell stdin pipeline contained literal question marks instead of Chinese. The controller repaired those documents using UTF-8 file edits, checked actual readable text and reran strict OpenSpec. No product code or tests changed during that repair.

Delivery entry: PR #143, https://github.com/Amazinnn/Lesson-Kit/pull/143. Its merge commit and final CI remain recorded by GitHub. The sibling `revisit-paper-answers-and-edit-self-rating` remains planning-only.

OpenSpec CLI archived the completed change as `2026-10-17-align-paper-execution-status`, adding one requirement without modifying or removing existing requirements/scenarios. Post-archive strict all validation: **26/26 passed**.
