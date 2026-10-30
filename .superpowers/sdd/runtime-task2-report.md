# Task 2 implementation handoff — 2026-10-30

Scope: stable-runtime-live-reload tasks 1.2, 2.1–2.3, 3.1. Stage1 runtime_source.py preserved. No primary checkout, global installation, real registry, live3081, schemas or frozen pipeline contracts modified.

## Implementation
- Explicit preview/default-primary imports through target cwd+PYTHONPATH; supervisor owns HTTP Popen and metadata; daemon reuse/stop verifies listener identity. Legacy live unknown Python remains diagnosed; unrelated executable plus closed expected listener clears stale record without signalling it.
- HTTP condition closes mutation admissions, drains preexisting writes, then Bridge lock checks active/queued/waiting/approval ownership and closes provider admission. Final closure refuses new ordinary GETs too; all admitted handlers drain before shutdown. Internal owner controls bypass admission and require a local credential.
- 0.5s metadata watch with two matching observations; syntax and target entry-import preflight; unchanged snapshot recheck before shutdown; broken edit preserves old worker and retries only changed source. Fresh bytecode lookup directory prevents same-second stale imports. Assets update generation without replacing worker.
- Browser polls every1s; stable input/session selection restoration emits no action events. IME, unresolved fetch writes, existing Agent unknown outbox/approval states defer. Asynchronously rebound Paper/goals/experience input deliberately defers while dirty, rather than restoring before data bootstrap or into another item. Hidden closed forms do not block refresh. No automatic sends/submits.
- Runtime endpoint ownership + manual/architecture/glossary/action graph synchronized; frontend watch:editor uses existing Vite build.

## Evidence
- Initial admission tests failed missing runtime module, then2 passed green. Held-GET real ThreadingHTTPServer regression proves serve_forever stays alive until held GET completes despite daemon request threads. Mutation gate race and Bridge queued/waiting/approval ownership checks included.
- Focused regression command: python -m pytest tests/workbench/test_cli_daemon.py tests/workbench/test_cli_surface.py tests/test_runtime_admission.py tests/test_runtime_process.py tests/workbench/test_runtime_source.py -q
- Isolated real subprocess test copies source to temp, explicit --project-root, free port, isolated LESSONKIT_WB_HOME: actual worker controlled active Bridge ownership -> pending busy with same PID -> idle permits replacement; invalid syntax preserves PID/error; valid correction replaces PID; assets bump only assets generation; owned shutdown exits worker+supervisor. Fixture failure cleanup uses owned supervisor process tree on Windows.
- Actual Playwright browser fixture with generated CodeMirror adapter: text 'unsent 中文', selection[2,5], readonly 'submitted', submit count0 survived refresh. IME prevented reload then compositionend resumed it (3 total page loads). Runnable replay: tests/runtime_browser_check.js, read-only python http.server38971 at checkout root, browser_run_code_unsafe filename. Browser closed after verification.
- Additional actual async Paper bootstrap browser fixture: server initialized textarea after200ms; learner changed draft; generation change kept1 page load and text intact with visible refresh deferral. No premature restore. This check was executed interactively, not a full production Paper integration test.
- python -m compileall -q workbench passed. openspec validate stable-runtime-live-reload --strict passed. git diff --check passed.

## Boundaries / acceptance remaining
- Independent full repository suite, guards, real course acceptance and final adversarial lifecycle review belong to task3.2 and remain unchecked. No merge/archive/deployment.
- Browser tests use routed metadata and real generated editor, not a real provider or production course. No claim of complete UI/manual acceptance. Pending dynamic turn editor restoration follows matching data-turn-id; full queued editor async bootstrap acceptance remains for reviewer.
- Abrupt external TerminateProcess of the supervisor cannot run Python finally; normal stop uses authenticated HTTP graceful drain. Startup timeout explicitly cleans its owned process tree on Windows. An external force kill is outside normal safe-stop path.
- If preflight succeeds but replacement fails for a later environmental change, supervisor exits without a restart loop; no last-good source copy or source rewrite is maintained. Source correction and explicit restart are then needed.

## Commits
dbbf92ed feat: supervise runtime source and drain safe live updates.

Final focused regression:54 passed in21.24s. Documentation and task handoff committed separately.
