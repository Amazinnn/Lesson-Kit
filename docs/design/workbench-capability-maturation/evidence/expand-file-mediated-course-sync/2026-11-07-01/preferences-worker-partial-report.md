# P01 report — task 2.6 confirmed course learning preferences

Status: IN PROGRESS (implementation). Coordinator owns OpenSpec deltas, canonical docs, surface
registration and commits; this file records only what the implementation can prove.

## Scope actually touched

| File | Change |
|---|---|
| `workbench/data/course_preferences.py` | new Data writer/reader |
| `workbench/server/course_preferences_api.py` | new thin GET/PATCH adapter |
| `workbench/server/app.py` | two route registrations only |
| `workbench/server/static/workbench.js` | preference hydration + explicit save |
| `workbench/server/static/paper-practice.js` | reveal preference consumption |
| `tests/workbench/test_course_preferences.py` | new Python regression |
| `tests/workbench/course-preferences.test.js` | new node regression |

Nothing else in the tree was edited by this run (no shared docs, no OpenSpec task boxes, no
commits).

## Pre-implementation evidence (red)

Recorded before any implementation file existed, at checkout `c5a9c642` + the coordinator's
uncommitted FILE_CONTRACT/DATA_MODEL paragraphs.

```
python -m pytest tests/workbench/test_course_preferences.py -q
13 failed, 1 passed in 5.03s

node --test tests/workbench/course-preferences.test.js
tests 12 / pass 3 / fail 9
```

The three JS tests that passed already describe behaviour that must not regress: an explicit
setup choice wins, a continuing execution keeps its frozen `reveal_timing`, and a Paper with no
confirmed projection keeps the setup default.

## Contract pointers read

- `openspec/changes/expand-file-mediated-course-sync/proposal.md`, `design.md`, `tasks.md` (2.6),
  `specs/file-course-sync/spec.md` (Learning preferences are consumed),
  `specs/workbench-ui/spec.md` (Received course preferences win, Preference persistence fails).
- `docs/design/workbench-capability-maturation/{execution-guide,data-exchange-matrix,packages/wp01,contract-reconciliation}.md`
  (CR03 is the ledger row for this task).
- `docs/DATA_MODEL.md` “Confirmed course learning preferences (WP01)” and
  `FILE_CONTRACT.md` “Course exchange implementation boundary (WP01 in progress)” — both
  uncommitted coordinator edits at the time of writing.

(Implementation details, commands and results are appended below as each step completes.)
