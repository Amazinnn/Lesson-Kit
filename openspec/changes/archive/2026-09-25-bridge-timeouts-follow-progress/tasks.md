# Tasks

## 1. Confirm contracts

- [x] 1.1 Read the proposal, design, and spec delta; confirm the three timeout sites (`pi_rpc.stream`, the print-mode `Timer`, `expire_idle`) and the live `bridges.json` value (`timeout_s: 300` for Pi).
- [x] 1.2 Keep the change additive: prompts, session resume, cancellation, the "no transcript for a timed-out turn" rule, and one-turn-at-a-time serialization all stay as they are.

## 2. Silence-based budgets in the Pi transport

- [x] 2.1 Failing tests: a stream that keeps emitting past its budget completes; silence past the budget still raises; a command in flight gets the longer budget; an expired tool budget still fails.
- [x] 2.2 Track in-flight tool calls (`tool_execution_start`/`tool_execution_end`, cleared on turn/agent end) and choose the budget for the next read from that state.
- [x] 2.3 Re-export `IDLE_SECONDS`/`TOOL_SECONDS` from `conversation_providers` so the transport and the provider layer share one number.

## 3. Print-mode watchdog

- [x] 3.1 Failing tests: output past the silence budget is not a timeout; a quiet command survives on the tool budget; a quiet command still fails by its own budget.
- [x] 3.2 Replace the fixed `threading.Timer` with `_TurnWatchdog`: touch on every stdout line, observe normalized activities, one short tick.
- [x] 3.3 Switch to the tool budget only for `command`/`tool` activities by id — the turn-level progress activity is `running` for the whole turn, so a status-only rule would put every print turn on the tool budget (found by the existing `timeout_s=0.1` test).

## 4. Configuration and reporting

- [x] 4.1 `registry.add_bridge(..., tool_timeout_s)` stores the key only when given; `bridge add --tool-timeout` accepts it and prints the effective pair.
- [x] 4.2 `discover()` normalizes both budgets: tool ≥ silence, and for Pi below the 30-minute RPC idle window that recycles the process.
- [x] 4.3 `bridge list` reports `silence=`/`tool=` for every provider.
- [x] 4.4 Tests: the override round-trips, absence stays absent, and the normalization holds for default/custom/Pi-capped cases.

## 5. Documents

- [x] 5.1 CONTRIBUTING "Pi specifics": the two budgets, how to set them, and the Pi ceiling with its reason.
- [x] 5.2 ARCHITECTURE (bridge tree + the conversations bullet), REQUIREMENTS (Agent 对话与 Pi 活动).
- [x] 5.3 ACTION-GRAPH: L1 (conversations + provider config rows), L3 (two CLI rows + changelog entry), L4 W4 (the failure edge split).
- [x] 5.4 PRODUCT-MANUAL: what counts as 卡住, the two defaults, and how to change them.

## 6. Verification

- [x] 6.1 Repository checks on the working tree (see Evidence).
- [x] 6.2 Isolated acceptance on `%TEMP%/lk-to2` (scratch registry + a **copy** of the repo pool) with a stub provider: long answer over budget → done, stall → `provider timed out`, quiet command → done.
- [x] 6.3 Real Pi turn with a 20s silence budget and a 45s silent command.
- [x] 6.4 Real pool and real registry read-only throughout.

## What changed

- `bridge/conversation_providers.py`: `IDLE_SECONDS` (30 min), `TOOL_SECONDS` (20 min),
  `DEFAULT_IDLE_SECONDS` (300s), and `_budgets()` — the single place both budgets are
  normalized; `discover()` reports `timeout_s` and `tool_timeout_s`.
- `bridge/pi_rpc.py`: `stream(timeout, tool_timeout=None)` yields records and resets the
  clock on each one, using `tool_timeout` while a tool call is in flight
  (`_track_tools`); the constants are re-exported from `conversation_providers`.
- `bridge/conversations.py`: `_TurnWatchdog` replaces the print-mode `threading.Timer`
  (touch per line, `observe` per normalized activity, `command`/`tool` in flight →
  tool budget); the Pi path passes both budgets to `stream`.
- `registry.py` / `cli/main.py`: `bridge add --tool-timeout`, and `bridge list` shows
  both effective budgets.
- Docs: CONTRIBUTING, ARCHITECTURE, REQUIREMENTS, PRODUCT-MANUAL, ACTION-GRAPH L1/L3/L4.

## Evidence (2026-09-25)

Repository checks on the working tree: pytest **639** (630 before this change; +9 new
tests), Node **116** (unchanged), `compileall` exit 0, `openspec validate --specs
--strict` **11 passed**, `openspec validate bridge-timeouts-follow-progress --strict`
valid, `doctor` all checks passed, `guard extract-problems` PASS, `guard problem-set`
PASS.

New coverage: `test_pi_rpc.py` (+4) — a `chatty` turn outlives its 0.5s budget
(asserted by elapsed time) and settles, 1s of silence fails under a 0.2s tool budget,
the same silence succeeds with `stream(0.2, 5)`, and a command that never returns still
fails by its own budget. `test_conversations.py` (+3) — a print-mode turn emitting
progress for ~0.6s under a 0.3s budget finishes `done` (elapsed asserted), a command
silent for 1s survives with `tool_timeout_s: 10` and still fails with `tool_timeout_s:
0.2`. `test_conversation_providers.py` (+1) — defaults, the tool-raised-to-silence
rule, and the Pi ceiling. `test_registry.py` (+1) — `tool_timeout_s` is optional and
round-trips. The pre-existing `timeout_s=0.1` test is the regression pin for "a stall
is still a stall"; it failed against the first version of the watchdog (the turn-level
progress activity had flipped every turn onto the tool budget) and passes now.

Isolated acceptance (`%TEMP%/lk-to2`: `LESSONKIT_WB_HOME` scratch registry, a **copy**
of the repo pool migrated with `migrate-progress.py`, server on **port 3091**, never
the user's 3081; the provider is a `codex.cmd` shim that runs a stub turn):

- Silence budget 2s, tool budget 20s, driven through the real HTTP API
  (`/ai/sessions` → `/turns` → poll): a turn emitting 20 progress lines over **8.3s**
  finished `done` (the old code failed it at 2s); a turn that went quiet finished
  `failed`/`provider timed out`; a command silent for 6s finished `done` on the tool
  budget.
- **Real Pi agent**, `--timeout 20 --tool-timeout 90`: a prompt asking Pi to run
  `python -c "import time; time.sleep(45)"` and then answer completed `done` in
  **48.4s** with the answer `命令已跑完`, and the event stream shows the command row
  (`运行命令 · python -c "import time; time.sleep(45)"`) as the work it waited on.
  Under the previous total-time budget the same turn would have died at 20s.
- The real pool (`pool/dmath.db`, mtime Sep 20), the user's two course pools, and the
  real `~/.lessonkit-workbench/bridges.json` were **not written**: the copy differs
  only by the migration (589,824 → 868,352 bytes of added columns), and the registry
  still pins Pi at `timeout_s: 300` with no `tool_timeout_s` — which now means 300s of
  silence and 1200s for a command in flight, so the reported failures stop happening
  without touching the user's config.
- Scratch server stopped afterwards; no orphan Pi process (`node.exe` with
  `pi-coding-agent` in its command line) was left behind.

## Remaining limits

- A print-mode provider that is a Windows `.cmd` wrapper (npm-installed CLIs) is
  terminated as the wrapper process; its child can outlive the terminate and hold the
  output pipe, so a stalled print turn **reports** its timeout only when that child
  exits (measured: a 2s budget reported at 8.2s because the stub's child slept 8s). The
  status and the reason are always correct — only the moment of reporting slips. This
  predates the change (the old `Timer` stopped the process the same way) and does not
  affect the Pi path, whose RPC process is closed directly. A tree kill
  (`taskkill /T`, or reading stdout through a queue so the loop can leave early) is the
  fix, deliberately not folded into this change.
- `expire_idle` still recycles an RPC process after 30 idle minutes; a turn inside a
  quiet command is protected only because `tool_timeout_s` is normalized below that
  window. Raising the idle window without raising this ceiling would reintroduce the
  recycle-under-a-turn race.
- The ingest provider session keeps its own subprocess timeout; it bounds producing an
  artifact rather than a conversation turn and was not changed.
- The defaults apply to every provider: a Pi turn may now stay in `running` for up to
  20 minutes inside one quiet command before failing. That is the requested behaviour
  ("执行候时很久的命令…不能够截停"), but it does mean a wedged command is visible for
  longer than before.
