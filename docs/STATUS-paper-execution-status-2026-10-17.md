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

`openspec validate align-paper-execution-status --strict` passed. The acceptance agent still owns full-suite and isolated browser/API acceptance, repository-wide compile/extraction gates, and release/archive checks. Those checks have not been run by this implementation handoff.
