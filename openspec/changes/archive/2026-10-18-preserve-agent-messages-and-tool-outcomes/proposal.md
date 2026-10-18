## Why

The conversation UI shows a submitted message before the server responds, but durable history currently mirrors only successful exchanges. A rejected or lost response can therefore leave the learner unsure whether the message was accepted, and provider failure can remove the message from reopened history. Provider activity also lacks a consistent semantic outcome and safe recovery description.

## What Changes

- Persist accepted message text, submitted context, and optional client submission identity in the existing turn artifact before provider dispatch. Resolve repeated identities to the original turn and reject changed submitted payloads.
- Include accepted turns in conversation history even without a successful transcript exchange. Keep legacy successful transcript reads unchanged and do not fabricate missing legacy failure text.
- Keep an unsent or uncertain message in browser storage until acceptance is confirmed. Reconcile uncertainty with the same identity; retrying an accepted failure creates a new linked turn only after an explicit learner action.
- Render normalized provider activities with a semantic action, actual status, evidenced outcome/impact, and folded redacted diagnostics. Offer only recovery actions the backend supports.

This change preserves the existing one-active-turn gate. Queueing, interruption, running-send settings, new Paper reset approvals, and global history changes are outside its scope. The broader lifecycle proposal delegates its message-reliability and Tool Call Card requirements here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ai-teacher-bridge`: durable accepted messages, idempotent acceptance, and truthful failed-turn history.
- `workbench-ui`: durable local send recovery and evidence-based activity cards.

## Impact

Reuse `.lessonkit/jobs/conv-NNN/turn-NNN.json`, existing event files, `transcript.jsonl`, and provider normalization. Add an optional `submission_id` to the existing turn endpoint; callers that omit it retain current behavior. Update `FILE_CONTRACT.md`, the existing Tool Call Card glossary entry, the Agent manual section, and Action Graph history. No SQLite field, provider process, new persistence service, or global history format is introduced.
