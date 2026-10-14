## Why
Agent-composed papers currently stop at exported manifests and sheets. Learners expect saved papers to appear in the existing Workbench list, but the Agent has no documented managed-save command.

## What Changes
- Add `lesson-kit papers <workspace> save --input <manifest>` using the existing saved-paper writer.
- Return the saved paper ID, title, count and workspace-relative page URL only after successful persistence.
- Document the distinction between exporting a manifest and saving a reusable paper in the Agent practice contract.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `practice-set-export`: explicit managed saving of an existing practice manifest through the Agent CLI.

## Impact
Thin CLI extension, existing Data practice-set validation/writer, Agent contracts, surface ownership and corresponding documentation/tests. No new dependencies, SQLite writes, schema changes, grading changes or dialogue action protocol.
