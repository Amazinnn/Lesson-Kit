# Agent UI final acceptance ? 2026-10-16

Dated acceptance snapshot; the owning OpenSpec specifications and responsibility documents remain authoritative.

PR #139 retains the selected Agent conversation across middle-view navigation and same-tab refresh. Review found and repaired transient-read selection loss, stale same/different-conversation responses, provider-picker intent being overwritten, and current selected-load errors without feedback. Confirmed missing conversations return to the list; temporary errors preserve selection with a recoverable message.

The follow-up repairs the PR135?137 live Paper preview lifecycle: tab-scoped identity includes workspace, conversation, route and Paper; refresh restores only the current live preview. Conversation changes, new turns from either composer or goal assist, explicit collapse and navigation clear the relevant marker. Explicit reopening can retain a current live preview; replayed historical cards do not become live. Existing managed Paper records remain authoritative. No course-data or Python changes were required.

## Independent acceptance

- PR139 code/spec review passed at `e8deb5784248013ffef15bae4305015425ad0d29`, after deterministic red-green tests for the request ownership matrix.
- Combined PR135?137 review identified missing refresh persistence and a cross-conversation preview race. Preview repairs and caller coverage passed independent code/spec review at `044a24f78ca52ec8bdb879c44e0da12697095a01`.
- Final integrated code: `80b06d74474921c4cb8aaa21550bbb4f10b089f9`. Independent Node validation: 196 passed, 0 failed; strict OpenSpec: 24/24; whitespace check: clean.
- Isolated `PYTHONUTF8=1 python -m pytest tests -q`: 1009 passed in 181.92 seconds. The gate started at `d5e90fff`; no Python paths changed through final integration. Compileall passed when run sequentially after pytest; the first concurrent attempt encountered a transient bytecode rename collision. The dmath/ch06 extract-problems guard passed.
- OpenSpec tasks 4.1?4.3 are reconciled with this evidence. The accepted deltas are already in the live specs, so archive with `openspec archive agent-ui-v1-implementation --yes --skip-specs`; validate all remaining changes and specs afterwards.

## Runtime verification and handoff

The port 3081 server runs from this checkout and already serves the merged PR135?137 UI. The root URL is the workspace hub; Agent rail changes appear on workspace routes such as `/w/lesson-kit/practice`. Served assets matched the checkout during diagnosis. The browser's active URL was not observable; Ctrl+F5 on the workspace page loads current assets. No restart was required. All eight saved conversations were idle and the server had no provider children at inspection. Existing course data, backups and unrelated untracked artifacts were preserved.

The earlier `2026-10-16-pr135-137.md` snapshot records the original merge stage; its open acceptance tasks are closed by this later evidence. Remote PR-head and merge-commit CI are checked separately during integration; final status is reported from GitHub, not inferred from this local acceptance record.
