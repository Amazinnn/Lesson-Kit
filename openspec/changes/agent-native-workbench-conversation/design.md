## Context

The current bridge launches configured one-shot commands for `explain` and `diagnose`. The right column requires a current problem and displays those operations as chat-like buttons, but does not resume a provider conversation. Pool reads and writes are scattered across narrow commands, so a native Agent cannot safely search, govern candidates, or make an explicit structured edit.

## Data CLI decisions

1. Add `wb data <workspace>` with JSON stdout for `get`, `list`, `search`, `history`, `create`, `update`, `delete`, `state`, `gate`, and `promote`. Entities are `kp`, `problem`, `candidate`, and `relation`; aliases may be accepted but canonical output uses these names.
2. Read operations are zero-write. Mutations require JSON from `--input <file|->`, an explicit state value, or an explicit object id. Ordinary conversation never infers a write.
3. A new additive `content_sequences(scope, entity_type, next_value)` table assigns readable IDs within the active course/chapter. Existing numeric suffixes seed the first value; no hash is used.
4. Formal problems cannot be created directly. Candidates may be created, edited, gated through existing repository scripts, and promoted only after both gates pass. Editing candidate content resets both gates to pending.
5. Physical deletion is one SQLite transaction. Problem deletion removes progress, attempts, feedback, schedule, current state, and signals. Knowledge-point deletion removes relation rows and that membership from multi-owned problems; newly ownerless problems receive the same cascade. Relation deletion removes only the relation. No tombstone or deletion event is created.
6. `history` is a joined read of existing learning records; it creates no new session or content log. An explicit state edit reuses the existing current-state/schedule rule and still creates no feedback or signal event.

## Provider and conversation decisions

1. PATH discovery exposes `codex` and `claude` when present; optional registry entries override only arguments, model, and timeout. A new conversation selects one provider and never switches automatically.
2. Codex uses stable `codex exec --json` and `codex exec resume`; Claude uses print/resume stream-json. Both run with the workspace as cwd, inherit local authentication/configuration/skills/project rules, and receive an appended Lesson Kit teacher contract plus authoritative context.
3. `.lessonkit/jobs/conv-###/conversation.json` stores provider, provider session id, timestamps, and current status. Per-turn event files support polling while running. `transcript.jsonl` receives only successful explicit user/assistant exchanges with context anchor and change summary. Drafts, navigation, tool traces, failed output, and cancel output are not copied into the durable transcript.
4. Provider output is parsed into normalized monotonically sequenced events. Claude text partials are surfaced when emitted; Codex uses stable JSONL phase/text events. Only one running turn is allowed per conversation. Cancellation terminates that process and reports `cancelled` without creating or switching a provider session.
5. Provider session loss, nonzero exit, timeout, parse failure, and cancellation are reported literally. No automatic retry with a new session or other provider occurs.
6. Provider-native storage remains the complete conversation authority. Lesson Kit's mirror is intentionally smaller and exists for workbench navigation, context anchors, and successful exchange display.

## Context and UI decisions

1. The browser sends a message plus route, page type, selected object id, current graph filter/selection, three recent object identifiers, and an explicit include-draft flag. It never submits the entire DOM.
2. The server re-reads the named workspace and constructs authoritative context: fixed workspace/course/chapter/route/page type; current problem and submitted practice records; knowledge-point content/state/signals/schedule/neighbours/problems; or graph filter, selected node, and relation summary.
3. Unsubmitted practice answer/notes are excluded by default. A practice-only checkbox may attach the current draft for that turn; the draft is not written elsewhere.
4. The right column removes visible explain/diagnose shortcuts but preserves their APIs. It shows provider/session controls, recent ten conversations, new conversation, messages, optional draft checkbox, input, send, and a temporary stop control.
5. The optional daily-new-session setting lives in browser local storage and defaults off. When enabled, the first entry on a new browser-local date creates a session only if no turn is currently running.
6. A successful Agent content mutation ends with a compact object/action/link summary. When it affects the visible anchor, the browser re-reads the relevant model; structural changes may perform a controlled page refresh while preserving the conversation id.

## Compatibility and boundary

- Existing explain/diagnose jobs, APIs, CLI flags, routes, storage keys, feedback writes, and current-state behavior remain.
- The only old-range source change is the approved additive `pool_schema.py` sequence table. `pipeline/`, `pool/scripts` behavior, and `lessonkit.py` are unchanged.
- No SDK, daemon, npm package, framework, hash, automatic learning log, or cross-provider fallback is introduced.
