# 2026-10-14 Agent managed paper save

Added `lesson-kit papers <workspace> save --input <manifest>` through the installed extension dispatcher. It validates an existing practice-set manifest, checks its selected course, and delegates atomic JSON persistence to the existing Data writer. The receipt reports the saved ID, title, count, and browser page URL.

The Agent practice contract now distinguishes exported manifests and printed sheets from managed papers and requires the successful JSON receipt before claiming a save. Interface ownership, file/data contracts, architecture, task routing, manual, and action graph were synchronized.

Focused fixture evidence: the command preserves ID order and request metadata, appears in the browser list, leaves the source manifest and existing papers untouched, and leaves SQLite bytes unchanged. Invalid manifests and an absent database return exit 2 without creating saved papers or a database.
