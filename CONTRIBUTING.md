# Contributing

Lesson Kit's runtime remains standard-library-only. The editable development
install adds only the test runner and exposes the `wb` command.

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
