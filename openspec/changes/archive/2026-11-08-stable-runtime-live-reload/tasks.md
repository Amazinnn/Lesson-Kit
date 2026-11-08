## 1. Runtime source
- [x] 1.1 Source selection and watch snapshot primitives with failing tests
- [x] 1.2 Explicit runtime command source, child import path and identity diagnostics
## 2. Live update
- [x] 2.1 Supervisor/worker lifecycle and safe Bridge/request admission drain; add a held-GET regression proving shutdown waits for all admitted GET and mutation handlers despite default daemon request threads
- [x] 2.2 Python/asset debounce, broken edit preservation and rollback
- [x] 2.3 Browser pending/error notices and draft-safe refresh
## 3. Delivery
- [x] 3.1 Focused subprocess/browser checks and responsibility docs
- [x] 3.2 Independent full-suite and real isolated acceptance
  - Full suite: repeated green runs after every later change landed on the same
    main (1,582 passed / 432s most recent; 1,577 / 1,572 / 1,559 in earlier
    rounds), compileall, Node 297 assertions, live specs strict, extract-problems guard.
  - Real isolated acceptance: supervisor/worker exercised through the real
    subprocess harness (`tests/test_runtime_process.py::test_real_reload_invalid_edit_assets_and_stop`,
    4/4 standalone re-runs), and real daemon probes on isolated ports (3097/3098)
    verifying `/api/runtime` source identity, supervisor/worker pids and
    reload state — recorded in
    `evidence/align-runtime-source-with-installed-code/2026-11-08-acceptance/runtime-source.json`
    and independently reviewed in
    `evidence/mature-course-content-operations/2026-11-09-acceptance/independent-review.md`.
  - The later `align-runtime-source-with-installed-code` change (archived) owns
    the default-source rule; this change keeps override/provenance/live-update
    semantics, which the same battery covers.
