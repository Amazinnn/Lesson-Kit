# 2026-10-14 Agent managed paper save

Added `lesson-kit papers <workspace> save --input <manifest>` through the installed extension dispatcher. It validates an existing practice-set manifest, checks its selected course, and delegates atomic JSON persistence to the existing Data writer. The receipt reports the saved ID, title, count, and browser page URL.

The Agent practice contract now distinguishes exported manifests and printed sheets from managed papers and requires the successful JSON receipt before claiming a save. Interface ownership, file/data contracts, architecture, task routing, manual, and action graph were synchronized.

Focused fixture evidence: the command preserves ID order and request metadata, appears in the browser list, leaves the source manifest and existing papers untouched, and leaves SQLite bytes unchanged. Invalid manifests and an absent database return exit 2 without creating saved papers or a database.

Independent acceptance: 997 Python tests, 164 Node tests, strict OpenSpec24/24, compilation and extract guard passed at 6e21281. The two initially observed Pi fixture failures did not reproduce on candidate or baseline; their original cause is unproven. Docs-only L3/L4 repair b204a13e passed independent review and strict validation. Optional problem-set guard was not applicable because its output was absent. Runtime adoption requires the new CLI and save instructions; an older running prompt remains unchanged until the normal idle service refresh. No active work is to be interrupted.
