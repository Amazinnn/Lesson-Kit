## Why

A turn's budget is total wall-clock time. For Pi, `process.stream(timeout_s)`
computes one deadline for the whole run and never extends it; for Codex and
Claude a `threading.Timer` kills the process after the same fixed interval. Both
default to 300 seconds and a pinned provider keeps whatever `bridge add` stored.
The result is that any turn which takes longer than the budget fails as
`provider timed out` **however much progress it was making**, and because the
process is stopped on timeout, a long-running command dies with it. Every
multi-chapter import, OCR pass, or large print is at risk — observed live: three
consecutive Pi turns in this repository failed at exactly 300s while the agent
was still emitting activity, and a 39 KB staged manifest import cannot finish
inside that window.

## What Changes

- A budget measures **silence, not duration**: every provider record or output
  line resets the clock, so a turn that keeps working is never timed out for
  taking a long time.
- While a command or tool call is in flight, the longer **tool budget** applies,
  so a slow command that prints nothing for minutes is not cut off mid-run.
- The idle process window stays longer than the tool budget, so a turn that
  really is stuck fails with its own timeout reason before the Pi process is
  recycled under it.
- Both budgets are configurable per provider (`timeout_s`, `tool_timeout_s`) and
  reported by `bridge list`, with the existing 300s kept as the silence budget
  so nothing becomes stricter than today.

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`: turn budgets follow provider progress, a running command
  gets the longer budget, and a stuck turn still fails honestly.

## Impact

Two bridge modules and their constants, one CLI flag, and the documentation of
the failure mode. No pool, schema, pool data, or UI change; provider commands and
normalization are untouched.
