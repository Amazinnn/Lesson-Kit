# Native task binding and test side-effect correction

2026-11-07, isolated codex/course-sync checkout, followup to9e24990c.

Task construction now uses native Windows XML and explicit executable/module/working-directory identity. Preflight verifies the source import root. Configuration is persisted only after successful creation; missing/partial media is rejected. Global schedule invocation parses correctly. Native processes are bounded and hidden; toast timeout returns not-delivered without discarding sync outcomes. Native command output uses the platform encoding.

The existing aggregation test was discovered to call real schtasks and had registered `LessonKit Course Sync` at14:43:25. Earlier statements that no system task was touched were incorrect. The exact task was queried, disabled, identity checked and removed. Tests now isolate task transport. This correction is a test side-effect fix, not a production hourly installation.

Focused CLI/task checks25 passed in60.83s; after encoding changes relevant subset13 passed in6.34s. compileall and change strict passed. The native probe created a unique task, updated, disabled, enabled and ran it, then removed it. Its wrapper set an isolated empty registry and invoked the real CLI; returned0, recorded actual CWD/source. It verifies native lifecycle, source binding and safe CLI invocation, not a real configured-course hourly run, real notification display or release cutover. No enduring task remains from these checks.

V04 independently reconciled the F2 fixture and failures; its report is a dated source snapshot. Subsequent format2/grouped-transaction plans remain unimplemented at this checkpoint and retain the original performance gates.
