## Why
Installed editable paths and PID-only daemon reuse hide stale source. The sole user needs immediate use after edits and safe rollback.
## What Changes
Default runtime follows the primary checkout; explicit --project-root previews a worktree. Report real source/process. Watch implementation and served assets, defer reload while Agent work is active, preserve browser drafts.
## Capabilities
### New Capabilities
- `runtime-live-reload`: source selection, provenance and safe live updates.
### Modified Capabilities
- `review-workbench`: dashboard/daemon/serve source and status diagnostics.
## Impact
Shell, Bridge admission, browser update client, CLI, documentation. No pool schema or frozen pipeline changes.
