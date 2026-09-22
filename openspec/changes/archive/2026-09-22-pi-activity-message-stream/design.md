# Design — Pi activity message stream

Pi keeps the existing normalized `activity` event and polling endpoints. The
normalizer classifies tool names into file-read, file-write, search, shell, or
generic tool records; Lesson Kit shell commands receive their own label.
Generic provider progress, reasoning lifecycle, and answer-generation rows are
not emitted for Pi.

The classifier is a Pi presentation adapter over the existing normalized
event contract, not a second protocol:

| Pi operation | Learner-facing action |
|---|---|
| read / view | Read file |
| write / edit / apply_patch | Update file |
| grep / find / search | Search |
| bash / shell | Run command |
| `lesson-kit` or equivalent module invocation | Operate Lesson Kit |
| any other concrete tool | Call `<tool name>` |

Provider-turn, thinking, answer, and other generic lifecycle phases produce no
activity message. Hidden reasoning and raw protocol objects are never eligible
for the learner-facing stream.

The browser chooses presentation from the conversation's provider. Pi creates
one compact message per activity id and updates it in place. Codex/Claude keep
the execution-plan component. A concrete activity closes the current Pi text
segment so later deltas open a new bubble in correct chronological order.

The browser keeps one ordered sequence of Pi text segments and activity ids.
Contiguous deltas append only to the current text segment. Receiving an
activity seals that segment; receiving later text allocates the next segment.
Activity status changes replace the existing row in place and never move it or
append a completion duplicate.

Details contain paths, queries, or sanitized commands, never write contents.
Output is bounded, sanitized, and collapsed for every status. Successful
transcripts retain coalesced concrete activities; failed/cancelled output stays
outside the successful mirror.

Sanitization and truncation happen once in the Bridge before event storage:
details are capped at 500 characters and output at 4000 characters after
assignment-style secret and bearer-token masking. There is no UI-only
redaction implementation. File-write summaries may expose
the target path but never the written body. Command arguments and output pass
through the same sensitive-value masking before event storage, so reopening a
conversation cannot reveal a value that the live row hid.

On reopen, the durable mirror restores the coalesced concrete activities and
the final successful answer under the current mirror contract; it does not
attempt to reconstruct every transient delta. Failed and cancelled turns keep
their live status only and add no long-term transcript activity.

## Compatibility and acceptance boundary

Polling remains 350 ms; no WebSocket, SSE, dependency, or provider command is
added. Pi alone receives the message presentation. Codex and Claude continue
using their current execution plan and existing restoration behavior.

The design and OpenSpec contract are frozen here. Deterministic browser tests,
the complete automated suite, and one real Pi 0.85.1 scratch turn are delegated
to the next Agent and remain unchecked in `tasks.md`. Live acceptance must use
an isolated registry, workspace, and pool copy.
