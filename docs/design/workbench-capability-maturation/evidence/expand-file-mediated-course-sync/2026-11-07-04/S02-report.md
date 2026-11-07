# S02 — scheduler / Git CLI audit (read-only)

Scope: `workbench/cli/course_sync.py`, `workbench/bridge/git_sync.py`, `workbench/surface.py`,
`workbench/data/course_sync.py` (cleanup only), `openspec/changes/expand-file-mediated-course-sync/*`,
`tests/workbench/test_course_sync*.py`, `pyproject.toml`.
No source/doc/test edits, no staging, no commits, no OS task creation, no network remotes, no real course data.
Only file written: this report.

Not a delivery claim. Parent owns `course_sync.py`; findings are handed over, not fixed.

---

## Confirmed bugs

### B1 (high, user-visible) — `_toast` never displays anything; every notification is silently dropped
`workbench/cli/course_sync.py:372-389` (`_toast`)

```python
subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script, title, message], ...)
```

`powershell.exe -Command <string>` concatenates every trailing argument into the *command text*; it does
not populate `$args`. The script therefore reads `$args[0]`/`$args[1]` as `$null` and the title/message
are parsed as extra statements → parse error, exit 1.

Isolated check (no toast shown, harmless script):

```
PS> powershell -NoProfile -NonInteractive -Command "'ARGS=[{0}]' -f ($args -join '|')" "dmath: 课程同步" "2 项"
At line:1 char:30
+ 'ARGS=[{0}]' -f ( -join '|') dmath: 课程同步 2 项
+                              ~~~~~~
Unexpected token 'dmath:' in expression or statement.
exit=1
```

Impact: spec `file-course-sync` "a single short conflict notification SHALL reflect actual outcomes" is not
met; `receipt["notification"]["notified"]` is always `false`, and because `_notice` still writes
`last-notice.json`, the dedup (B5) suppresses any later attempt. Every CLI test monkeypatches `_toast`
(`test_course_sync_cli.py:115,140,181,233,288`), so the real invocation is never exercised.

Minimal fix: stop passing the text as argv. Put `$env:LK_TOAST_TITLE` / `$env:LK_TOAST_MESSAGE` into the
child `env` and read them from the script (`$env:LK_TOAST_TITLE`), so no quoting is involved; also add
`timeout=` (see B8).

### B2 (high, hourly-run durability) — a Git failure raises `RuntimeError` past `run()`: no receipt, and one course kills the rest
`course_sync.py:78-80` (`run` catches only `ValueError/OSError/JSONDecodeError`),
`course_sync.py:446-449` (`_run_every_course` catches only `_InputError`),
`git_sync.py:43-45` (`_git` raises `RuntimeError` on any git failure), `git_sync.py:232`
(`fetch_remote` raises `RuntimeError`).

`_sync` calls `git_sync.fetch_remote` / `git_sync.publish`, both of which reach `_git`. An offline remote,
DNS failure, expired credential or `index.lock` produces `RuntimeError` → propagates through `_sync` →
`run` (no `except`) → `workbench/cli/main.py:1339-1346` `_run`/`main` (no `except`) → console script
traceback, exit 1. Consequences:

- no `last-receipt.json` is written (`_finish` never runs) — the run leaves no evidence at all;
- inside `_run_every_course`, the loop aborts on the first failing course, so remaining independent
  courses never sync — the spec scenario "independent courses complete" is violated by a single
  unreachable remote.

`tests/workbench/test_course_sync_git.py:413` proves `fetch_remote` raises `RuntimeError`, but no test
asserts what the CLI does with it.

Minimal fix: add `RuntimeError` to the `except` in `run()` (map to the receipt's `failed` / exit 2), and in
`_run_every_course` catch it per course with code 4 plus a `failures` entry, so later courses still run.

### B3 (high, data truth) — `sync` publishes the local package while a genuine conflict is unresolved
`course_sync.py:266-295` (`_sync`)

```python
if incoming is not None:
    inspection = ...; result = exchange.apply_exchange(...)   # conflicts are NOT applied
package_dir = Path(repository["repo"]) / package
exported = exchange.export_course(pool, workspace, package_dir)  # runs unconditionally
...
published = git_sync.publish(...)                                # runs unconditionally
receipt["status"] = _sync_status(receipt)                        # "conflict" recorded after the push
```

A two-sided change is detected, refused locally (correct), and then the local side is written over the
package and pushed. The branch tip loses the other installation's version; repeated hourly runs on both
machines keep overwriting each other, so the shared branch never carries both sides and the "choose a side"
step cannot be completed from the branch — only from the machines' local databases.

Spec `file-course-sync` "Reconcile versions and learning facts": "Genuine two-sided changes SHALL expose
differences and accept a single or batch side choice." The conflict path is only tested through `receive`
(`test_course_sync_cli.py:177-227`), never through `sync`.

Minimal fix: when `result["conflicts"]` is non-empty, skip export+publish (return the conflict receipt), or
at minimum skip `publish`.

### B4 (medium) — stale envelope deletions are never staged, so the repository stays dirty and keeps dead blobs
`workbench/data/course_sync.py:538-541` deletes replaced envelopes inside the package directory
(`stale = previous - written; unlink`), but `course_sync.py:324-331` (`_package_paths`) builds the managed
list from the **post-export** manifest only, and `git_sync.py:292` stages exactly those paths
(`git add -A -- <paths>` with `--literal-pathspecs`).

Result: the unlinked file is a worktree deletion that is never staged; the commit does not record it, the
blob stays on the branch, and `git status` stays dirty — which also makes `inspect_repository()`
(`git_sync.py:210`) report `repository_clean: false` forever. `test_course_sync_git.py:277` covers deletions
only when the caller passes the deleted path explicitly, which `_package_paths` never does.

Minimal fix: stage the union of the previous manifest's asset paths and the current ones (the previous
manifest is already read by `_materialize`), or stage `-A --` the validated package prefix.

### B5 (medium) — conflict notice dedup never re-arms
`course_sync.py:352-369` (`_notice`) returns early when there are no conflicts, leaving
`.lessonkit/course-sync/last-notice.json` untouched. Once an identity has been announced, resolving it and
conflicting on it again is never announced. `test_course_sync_cli.py:216-219` only covers "same unresolved
conflict twice".

Minimal fix: on an empty identity list, `path.unlink(missing_ok=True)` before returning.

### B6 (medium, scheduler source identity) — the task records `sys.executable -m workbench.cli.main`, not the installed command, and records no source root or working directory
`course_sync.py:411`:

```python
command = f'"{sys.executable}" -m workbench.cli.main course-sync {TASK_COMMAND}'
```

`schtasks /Create /SC HOURLY /TR <command>` (`:424-425`) sets no "Start in", so the task runs with
`%SystemRoot%\System32` as cwd; resolution therefore depends entirely on the current install mode.
Observed here:

```
python -c "import workbench"  (repo paths stripped from sys.path)
  -> D:\.codex\worktrees\course-sync\lesson-kit\workbench\__init__.py
lesson-kit -> D:\Python\Scripts\lesson-kit.exe   (pyproject: lesson-kit = workbench.cli.entry:lesson_kit_main)
```

The `workbench` package currently resolves through an **editable install pinned to this git worktree**.
So: (a) the installed task keeps importing from whatever checkout the editable install points at, including
a temporary worktree that may be deleted — after removal the task dies with `ModuleNotFoundError`, exit 1,
no receipt and (per B1) no notification; (b) a non-editable install would run a stale snapshot instead of
the checkout the user edits; (c) `lesson-kit.exe` on PATH is ignored even though `design.md:31` says the
task calls "同一已安装命令" (the same installed command). The receipt only echoes the string that was sent;
nothing verifies the stored task can run.

Minimal fix: resolve `shutil.which("lesson-kit")` and fall back to `sys.executable -m` only after probing
that `workbench` imports from a neutral cwd; record the resolved command plus the resolved `workbench` root
in the receipt, and fail `install` with an input error when the probe fails.

### B7 (low) — `schedule install` validates media only when a workspace is named
`course_sync.py:397-408`: the `install needs --repo and --path, or saved media` check sits inside
`if args.name:`, so `course-sync schedule install` with no workspace creates a task with no validation.
Also `_save_media` (`:406`) persists media before `schtasks` succeeds, so a failed install still changes
course config.

### B8 (low) — no subprocess timeout in the scheduled path
`_toast` (`:386-388`) and `_schtasks` (`:430`) call `subprocess.run` without `timeout=`; a hung
`powershell`/`schtasks` blocks the hourly run indefinitely. `_toast` also omits the
`hidden_launch_kwargs()` that `git_sync._git` (`git_sync.py:41`) uses to avoid console windows in a
non-interactive session.

---

## Unverified questions (no OS task created, per brief)

1. `/TR` quoting when the interpreter path contains spaces (`"C:\Program Files\...\python.exe" -m ...`).
   The local interpreter is `D:\Python\python.exe` (no spaces), so this installation is unaffected; the
   argv-list → `CreateProcess` → `schtasks` round trip is untested here. `test_course_sync_cli.py:276-277`
   only asserts the prefix of the argv.
2. `schtasks /Create /SC HOURLY` without `/ST`: which start time is stored, and whether a missed run is
   caught up. Not exercised.
3. Whether a WinRT toast can render at all from a Task Scheduler-launched process. Even after fixing B1
   this may fail in some session states; the current code would report `notified: false` (and per B5 never
   retry).
4. `--all-configured` from a neutral cwd: `_run_every_course` uses user-level registry entries, which
   look absolute, so no cwd dependency is expected — not executed.

---

## Test coverage: existing vs missing

Existing (relevant):
- `test_course_sync_cli.py`: export→check→receive receipt, input error, status, first publication,
  cross-installation receive, `receive` conflict + single notification + batch `--keep`, rejected push
  reported as partial, `schedule install` argv/media/`--all-configured`, `enable`/`disable`/`remove`
  argv, `--all-configured` aggregation of a success and a skipped course.
- `test_course_sync_git.py`: managed-path staging, literal metacharacters, `.git` aliases, credential
  sanitizing, no-op publish, unrelated worktree/staged files, rejected push without force, explicit
  deletions, branch checked out, binary-safe readback, directory/symlink refusal, fetch without touching
  the worktree, fetch `RuntimeError`, inspect read-only.
- `test_course_sync_data.py` / `_receive.py` / `_execution.py`: envelope fidelity, origin identity,
  inspection without state init, partial-unit recovery, retry without duplicates, publication failure
  resume, draft merge, deletion semantics.

Missing (each maps to a bug above):
- B1: any test that calls the real `_toast` (all tests monkeypatch it) — a unit test asserting the child
  env/script contract would be enough.
- B2: CLI-level Git failure → receipt + exit code; and one failing/conflicting course leaving the other
  configured courses running (`test_all_configured_aggregates_each_course_exit_code` only covers
  success + skip, `test_course_sync_cli.py:285-305`).
- B3: `sync` on both sides with a genuine two-sided change → conflict, and the remote branch must not
  receive the local package.
- B4: an export that cleans a replaced envelope → the deletion is committed (`publish` called through
  `_package_paths`).
- B5: notice re-arms after a resolved conflict.
- B6/B7: install twice (update), install with no workspace, install when `workbench` is not importable
  from a neutral cwd, and the recorded command's source root.

---

## Checks actually run (fixtures only)

1. `powershell -Command <script> a b` argument concatenation — reproduced the `$args`/parse failure (B1).
2. `python -c "import workbench"` with every repo path stripped from `sys.path` — resolves to the worktree
   through the editable install; `lesson-kit` resolves to `D:\Python\Scripts\lesson-kit.exe` (B6).
3. Static reads of the six files above plus `pyproject.toml`, `workbench/cli/main.py` (dispatch:
   `workbench/cli/main.py:954-961`, `_run` at `:1339-1346` has no exception handling), and
   `workbench/data/course_sync.py` cleanup lines.

No test suite was executed; no OS task was created, changed or deleted; no Git command was run.
