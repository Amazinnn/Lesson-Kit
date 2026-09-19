# ADR 0022: Background Workbench Service and the lesson-kit Command

## Status

Accepted (2026-09-17).

## Context

The workbench server has always been a foreground process: `wb serve` blocks
until Ctrl+C, and `wb open` only prints a URL. Three earlier records assumed
that shape and argued against going further:

- **ADR 0004** ("lightweight runtime state") closed with: "We will not
  introduce PyYAML, packaging metadata, dashboarding, eval harnesses, role
  bundles, or extension systems in this step."
- **FUTURE-DEVELOPMENT-NOTES** recorded the Heartbeat decision: "不做常驻后台
  服务，采用『每天首次打开时自动触发一次』的机制…应用未打开时不运行、不更新、
  不消耗 Agent 调用."
- **GLOSSARY** lists 常驻后台进程 under the _Avoid_ terms for 桥 / Bridge.

On 2026-09-17 the owner requested a first CLI surface: `lesson-kit init`,
`lesson-kit daemon start|stop`, `lesson-kit dashboard`. Two of those are
impossible while the server can only run in the foreground — closing the
terminal that started it ends the session, and there is no supported way to
launch it detached.

A second, unrelated finding shaped the implementation: the machine carries two
`pi` installations and two npm prefixes on PATH, so "which executable does the
bridge run" was decided by PATH ordering alone. A detached service also
inherits the environment of whatever launched it, which makes that ambiguity
worse. Both are addressed by the same change (see `bridge` config below).

## Decision

Introduce exactly one background lifecycle for the workbench server, and make
the CLI name explicit.

- `daemon start|stop|status` manages a **single** service instance on the
  fixed local port (3081 by default). `start` is idempotent.
- The recorded process id and log live under the user-level registry directory
  (`~/.lessonkit-workbench/`, honoring `LESSONKIT_WB_HOME`), beside
  `workspaces.json` and `bridges.json` — not inside any workspace, and not in
  a new location.
- `start` reports success **only after the port actually answers**. A service
  that dies immediately, or never binds, is reported as a failure with its log
  path.
- `stop` refuses to signal a recorded pid that no longer belongs to a Python
  process, clearing the stale record instead. (`os.kill(pid, 0)` is not used
  on Windows at all: it maps to `TerminateProcess`.)
- `dashboard` ensures the service is running and opens the workbench in the
  browser. It **does not add a fourth page**: DESIGN.md's anti-dashboard
  stance and the three-page model (practice / knowledge points / knowledge
  graph) stand unchanged.
- `lesson-kit` is a **second name for the same CLI**, not a second CLI. It
  shares every subcommand with `wb`; `lesson-kit init` is `wb init`.
- The bridge gains an explicit `command` override that **takes precedence over
  PATH discovery**, so a provider executable can be pinned rather than
  resolved by PATH ordering.

## Consequences

The "no resident background process" guidance is superseded **for the
workbench server only**, and its original intent is preserved: the daemon
performs no scheduled work and consumes no Agent calls while no client is
talking to it. Agent turns are still started only by an explicit HTTP request
from the workbench UI. The Heartbeat decision — no unattended recomputation —
is untouched.

Costs accepted:

- There is now a long-lived process to reason about. It is self-describing
  (`daemon status`, a pid file, a log) and never starts itself.
- A detached service inherits the launcher's environment, including PATH. A
  provider installed after the service started will not be visible until the
  service is restarted; `bridge list` exists to make that visible instead of
  silent.
- `lessonkit.py init` (runtime state for a workspace folder) and
  `lesson-kit init` / `wb init` (workspace registration) mean different
  things. The root CLI is frozen by AGENTS.md, so the collision is documented
  rather than resolved by renaming.
- Pinning `command` in `bridges.json` reverses a previously asserted behavior
  (`discover()` used to ignore a configured command). The spec delta and tests
  were updated with it.
