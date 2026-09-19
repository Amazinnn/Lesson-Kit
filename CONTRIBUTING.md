# Contributing

Lesson Kit's runtime remains standard-library-only. The editable development
install adds only the test runner and exposes the workbench CLI under two
equivalent command names, `wb` and `lesson-kit`.

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
wb --help
wb init . --course dmath --chapter ch06
wb serve
```

`lesson-kit` is the same entry point under a second name; `lesson-kit daemon
start|stop|status` runs the server detached and `lesson-kit dashboard` opens
it. Both names share every subcommand, so a change to one applies to both. Run
the CLI tests after touching either:

```bash
python -m pytest tests/workbench/test_cli_daemon.py tests/workbench/test_cli.py -q
```

**Name collision:** the project's `wb` script collides with the `wb` console
script shipped by Weights & Biases. Installing lesson-kit into an environment
that already has `wandb` overwrites that launcher (whichever was installed
last wins), and the `wb` command silently changes meaning. Prefer the
`lesson-kit` name, install into a virtualenv, or re-run
`pip install --force-reinstall --no-deps wandb` afterwards to give `wb` back
to Weights & Biases. `python -m workbench.cli.main` is always unambiguous.

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

- **Prompt delivery is unchanged.** The provider-agnostic teacher contract and
  page context are written to stdin every turn; Pi reads them in
  `--print --mode json` without a positional prompt (verified). The contract
  names only project-level things (`wb data`, the `lessonkit-action` block), so
  it does not assume any harness's tool names.
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
