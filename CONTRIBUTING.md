# Contributing

Lesson Kit's runtime remains standard-library-only. The editable development
install adds only the test runner and exposes the workbench CLI as the single
command `lesson-kit`.

## Development setup

Python 3.11 or 3.12 and Node.js 22 are the supported CI baseline.

```bash
python -m venv .venv
```

Activate `.venv`, then install the repository in editable mode:

```bash
python -m pip install -e ".[dev]"
```

The workbench CLI is now available from the repository root:

```bash
lesson-kit --help
lesson-kit init . --course dmath --chapter ch06
lesson-kit serve
```

`lesson-kit daemon start|stop|status` runs the server detached and
`lesson-kit dashboard` opens it. Run
the CLI tests after touching the entry point:

```bash
python -m pytest tests/workbench/test_cli_daemon.py tests/workbench/test_cli.py -q
```

**One name, on purpose:** the project ships only `lesson-kit` (module form:
`python -m workbench.cli.main`). It deliberately does **not** install the old
`wb` alias; every document, prompt, and example uses the same launcher.

## Configuring an Agent provider

Codex, Claude, and Pi are discovered from PATH. Pin an executable when several
installs of the same CLI exist, and set the model explicitly:

```bash
lesson-kit bridge add pi --command "C:/Users/you/.npm-global/pi.cmd" --model "deepseek/deepseek-v4-flash"
lesson-kit bridge list        # resolved path, [config] vs [path] source, missing-path marker
```

A configured `command` takes precedence over PATH discovery. Provider flags go
in `--args`; a value starting with a dash needs the equals form
(`--args=--no-tools`).

**Config is re-read on every request; code is not.** Editing `bridges.json`
(including the model) takes effect immediately without restarting the service.
Changing provider code — normalization, command building — does **not**: the
running service keeps the code it loaded at startup, and a long-lived daemon
will silently keep using old behavior. Restart it:

```bash
lesson-kit daemon stop && lesson-kit daemon start
```

### Pi specifics

- **Pi runs one hidden RPC process per conversation.** `bridge/pi_rpc.py` starts
  `pi --mode rpc`, frames strict LF JSONL, sends correlated `prompt`/`abort`
  commands, and keeps the process for 30 idle minutes (no process-count cap).
  Cancellation sends RPC `abort` first and only terminates when the run does not
  settle. A launch/handshake failure restarts once; a crash after the prompt was
  accepted fails the turn and is never replayed. Every provider child — Pi RPC,
  each Codex/Claude print-mode run, and the ingest provider session — launches
  with `CREATE_NO_WINDOW` on Windows, so no terminal window ever appears.
- **The teacher contract still arrives on stdin.** Codex and Claude read it as
  before; Pi receives the same text as the `prompt` command payload. The contract
  names only project-level things (`lesson-kit data`, the `lessonkit-action`
  block), so it does not assume any harness's tool names.
- **Pi loads `AGENTS.md` automatically** from the working directory and its
  ancestors, and context files are loaded regardless of project trust. The
  bridge runs the provider with the workspace as cwd, so the repository's
  `AGENTS.md` reaches Pi with no configuration.
- **Project trust gates everything else.** Non-interactive runs (`-p`,
  `--mode json`) cannot show a trust prompt, so with the default
  `defaultProjectTrust: "ask"` Pi **silently ignores project-level resources**
  (`.pi/settings.json`, `.pi/skills/`, project `.agents/skills/`). If you add
  any of those, either pass `--args=--approve`, save a decision in
  `~/.pi/agent/trust.json`, or set `defaultProjectTrust` in
  `~/.pi/agent/settings.json`. `AGENTS.md` is unaffected.
- **Pi's default system prompt is a coding-assistant prompt.** The workbench
  does not override it; the teacher contract arrives as the user message. If
  conversations skew toward coding behaviour, steer it with
  `--args=--append-system-prompt=<text>` (or replace it with
  `--args=--system-prompt=<text>`) rather than changing server code.
- The repository's `skills/<name>/SKILL.md` modules have no YAML frontmatter and
  are referenced **by path** (see `AGENTS.md` → 项目地图). Do not expect any
  harness to auto-discover them.

Frontend dependencies are needed only when rebuilding the checked-in editable
graph assets:

```bash
cd frontend/editable-graph
npm ci
npm run build
```

## Verification

Run the repository-level checks before opening a pull request:

```bash
python -m pytest tests -q
node --test tests/workbench/*.test.js
python -m compileall -q lessonkit.py workbench pipeline pool tests
```

Workspace artifact guards are separate from repository tests. Run them from a
workspace that contains the corresponding generated inputs and outputs.
