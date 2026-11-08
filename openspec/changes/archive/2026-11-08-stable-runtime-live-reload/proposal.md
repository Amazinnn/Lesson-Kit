## Why
Installed editable paths and PID-only daemon reuse hide stale source. The sole user needs immediate use after edits and safe rollback.
## What Changes
Default runtime source selection is owned by `review-workbench` (superseded here by `align-runtime-source-with-installed-code`); this change keeps explicit --project-root previews. Report real source/process. Watch implementation and served assets, defer reload while Agent work is active, preserve browser drafts.
## Capabilities
### New Capabilities
- `runtime-live-reload`: provenance and safe live updates.
### Modified Capabilities
- `review-workbench`: dashboard/daemon/serve status diagnostics (the source-selection requirement moved to `align-runtime-source-with-installed-code`).
## Impact
Shell, Bridge admission, browser update client, CLI, documentation. No pool schema or frozen pipeline changes.
