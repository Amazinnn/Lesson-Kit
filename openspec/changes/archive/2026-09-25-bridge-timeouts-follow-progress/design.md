# Design — Turn budgets that follow progress

## Where the limit lives

| Path | Site | Semantics today |
|---|---|---|
| Pi (RPC) | `conversations.py` → `pi_rpc.PiRpcProcess.stream(timeout)` | one deadline for the whole run: `deadline = monotonic() + timeout`, and every read shrinks the remaining budget. A turn that keeps streaming events for longer than the budget still dies. |
| Codex / Claude (print) | `conversations.py` → `threading.Timer(provider["timeout_s"], timeout_process)` | a hard wall clock over the whole process; on firing it marks the turn timed out and stops the process. |
| Pi process recycling | `pi_rpc.PiRpcRegistry.expire_idle` | closes a process idle for 30 minutes; a turn inside a silent tool call makes no records, so `_last_used` stalls and the process can be reaped mid-turn. |

`timeout_s` defaults to 300 in the registry, in `conversation_providers.get`, and
in `bridge add`; the ingest provider session has its own subprocess timeout with
the same default. On a timeout the agent process is discarded and closed, so any
command it was running dies with it — the failure mode the owner reports.

## The rule

**A budget measures silence, not duration.** Concretely, per provider turn:

1. every record (Pi) or output line (Codex/Claude) resets the clock, including
   the ones the mirror hides — thinking deltas, tool output updates, generic
   provider progress: activity is activity;
2. while a command or tool call is in flight the clock uses `tool_timeout_s`
   (default 20 minutes) instead of `timeout_s` (default 5 minutes), because a
   slow command is exactly the case that produces no output for a long time;
3. a turn with no record for the applicable budget fails as a provider timeout,
   reported through the existing failure path — the message and the mirror
   behaviour do not change;
4. `tool_timeout_s` stays below the 30-minute idle window so a genuinely stuck
   turn is failed by its own budget, with its own reason, rather than having its
   process recycled underneath it.

Nothing else moves: prompts, session resume, cancellation, the transcript rule
that a timed-out turn leaves no entry, and the "one turn at a time" serialization
all stay as they are.

## Implementation notes

- The Pi side tracks in-flight tools inside `PiRpcProcess.stream`: a
  `tool_execution_start` opens a call, `tool_execution_end` closes it, and the
  budget for the *next* read is chosen from that state. The record is inspected
  before normalization, so a hidden reasoning delta still counts as progress.
- The Codex/Claude side replaces the fixed `Timer` with a small watchdog that
  touches on every stdout line and switches to the tool budget while a normalized
  activity of type `command` or `tool` is running. The busy test is by *type*,
  not by status: the turn-level progress activity is `status: running` for the
  whole turn, so a status-only rule would put every print-mode turn on the tool
  budget and no stall would ever be caught (found by the existing `timeout_s=0.1`
  test, which now pins it). The watchdog keeps a short tick so a tiny configured
  timeout still fires promptly.
- Configuration stays additive: `timeout_s` (silence) and the new
  `tool_timeout_s`; `bridge add --timeout/--tool-timeout` writes them and
  `bridge list` reports both. Effective values are normalized where the provider
  is discovered — the tool budget is raised to at least the silence budget (a
  configured long silence budget must not shorten what a running command gets)
  and, for Pi, capped below the 30-minute RPC idle window.

## Compatibility and non-goals

- 300 seconds remains the default silence budget, so no working turn becomes
  stricter; what changes is that progress now extends it.
- Turning a timeout into a suspension is not the goal: a stuck provider is still
  failed and the process still stopped. The owner keeps the explicit 停止 button,
  and the abort-then-terminate path is unchanged.
- Not addressed here: the ingest provider session's own subprocess timeout, which
  bounds a different operation (producing an artifact) and keeps its own value.
