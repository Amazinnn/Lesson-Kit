# G01 report — system Git transport (task 2.8, transport portion)

Worker: DeepSeek implementation subagent (G01). Worktree: `D:/.codex/worktrees/course-sync/lesson-kit`, branch `codex/course-sync`.
Status: transport module + regression tests complete and green. Nothing committed (waiting for coordinator). No CLI/schedule wiring, no package acceptance claimed.

## Scope restated

- Layers: Shell → Domain → Data. `workbench/bridge/git_sync.py` is a side-attached Bridge that only runs when the coordinator requests transport. It does not import Data or SQLite, does no content comparison/merge, and raises no hidden fallbacks.
- Compatibility: new files only; no existing module, CLI surface, schema, prompt or canonical doc was modified. `FILE_CONTRACT.md`, `docs/GLOSSARY.md`, `docs/DATA_MODEL.md`, OpenSpec tasks/specs untouched.
- Owned files: `workbench/bridge/git_sync.py`, `tests/workbench/test_course_sync_git.py`, this report. Nothing else staged or edited (`git status` shows only these two new files).

## Baseline evidence (before implementation)

`python -m pytest tests/workbench/test_course_sync_git.py -q` → **14 failed**, every failure `ImportError: cannot import name 'git_sync' from 'workbench.bridge'`. Fixtures were already real temporary repositories (`git init --bare` remote + local working clone), so the failures isolated the missing behavior, not the harness.

## Final evidence

| Check | Command | Result |
|---|---|---|
| Transport regression suite | `python -m pytest tests/workbench/test_course_sync_git.py -q` | **passed** — 16 passed in 43.05s |
| Neighbor bridge suite untouched | `python -m pytest tests/workbench/test_agent_contracts.py tests/workbench/test_course_sync_git.py -q` | **passed** — 23 passed |
| Syntax | `python -m compileall -q workbench tests` | **passed** (exit 0) |
| Manual error paths | scratch script (deleted) | see "Error semantics" |

Not run (out of this worker's scope): full `pytest tests`, Node/browser suites, `openspec validate`, real remote host (GitHub) push, OS scheduled task, CLI receipt/exit codes. Suite runtime is dominated by real Git process spawn plus two intentionally unreachable-URL cases (9.5s / 3.1s); real repositories are used on purpose, no mocking.

## Public functions and return schemas (integration contract)

All functions take `repo` as the **working-tree root** (a subdirectory or a non-repository directory raises `ValueError` so managed relative paths can never be resolved against a foreign cwd). Every Git call is `['git', ...]` with `cwd=<root>`, `stdin=DEVNULL`, captured bytes, `GIT_TERMINAL_PROMPT=0` (fail instead of prompting inside an hourly task), and no shell.

### `inspect_repository(repo, branch, remote='origin')` — read-only

```python
{
  'repo': str,                # resolved working-tree root
  'branch': str,              # requested branch
  'remote': str,              # requested remote name
  'head_commit': str | None,  # detached HEAD is reported, not rejected
  'head_branch': str | None,  # None when detached
  'branch_exists': bool,
  'branch_commit': str | None,
  'branch_checked_out': bool, # head_branch == branch
  'repository_clean': bool,   # no staged, modified or untracked paths
  'staged_paths': [str],
  'modified_paths': [str],    # unstaged tracked changes
  'untracked_paths': [str],
  'remote_url': str | None,   # credentials replaced with '***@'
  'tracking_commit': str | None,  # refs/remotes/<remote>/<branch>, may be stale, no network call
}
```

No fetch, no `ls-remote`, no index/branch/ref writes; tests assert HEAD, `status --porcelain` and `for-each-ref` are byte-identical before and after.

### `fetch_remote(repo, branch, remote='origin')`

```python
{'repo': str, 'branch': str, 'remote': str, 'ref': str, 'commit': str}
```

`git fetch --quiet --no-tags --no-write-fetch-head <remote> +refs/heads/<branch>:refs/lessonkit/remote/<branch>`. The forced refspec touches **only** the private `refs/lessonkit/remote/` namespace, so: the user's branches, index, working tree and `FETCH_HEAD` are untouched; remote history rewrites are still readable for comparison (fetch never refuses with non-fast-forward); no reset/checkout/merge is performed. Tests assert unchanged local HEAD, unchanged dirty worktree file, unchanged `refs/heads`, and that remote bytes are readable at the returned commit.

### `read_remote_files(repo, commit, paths)` — binary safe

```python
{'commit': str,          # resolved full commit id
 'files': {relative_path: bytes},
 'missing': [relative_path]}
```

Uses `git ls-tree -z` + `git cat-file blob` (never `show <rev>:<path>`, so no pathspec ambiguity). Rules: unknown commit → `ValueError`; directory path → `ValueError`; symlink (`120000`) or gitlink (`160000`) entry → `ValueError`; absent path → listed in `missing`, never treated as a deletion. Tests cover raw PNG-like bytes with `\x00`/`\xff`, missing paths, directories, and a commit-tree symlink created via `git update-index --cacheinfo` (this account cannot create filesystem symlinks).

### `publish(repo, branch, managed_paths, remote='origin', message='Sync managed course files')`

```python
{
  'repo': str, 'branch': str, 'remote_name': str, 'managed_paths': [relative str],
  'local': {
    'status': 'committed' | 'unchanged',
    'commit': str | None,        # HEAD after the operation
    'created_commit': str | None,
    'previous_commit': str | None,
    'changed_paths': [str],      # empty when nothing was committed
  },
  'remote': {
    'status': 'published' | 'unchanged' | 'failed',
    'commit': str | None,        # verified remote refs/heads/<branch> after the attempt
    'reason': str | None,        # sanitized; push rejection text when failed
  },
}
```

Behavior, in order:
1. Validates the repo root, branch name, remote name and every managed path (explicit relative file paths only; `..`/absolute/drive-letter escapes, any `.git` component, symlinks and directories are rejected; containment is re-checked with `realpath`).
2. Requires `<branch>` to be the checked-out branch, else `ValueError` (names HEAD).
3. Refuses to run when the index contains staged paths outside `managed_paths` (`ValueError` listing them) instead of committing them. Untracked and unstaged changes are never staged or committed.
4. `git add -A -- <managed_paths>` — stages exactly those paths, so modifications, additions **and deletions** of managed paths are published.
5. Commits only if the index now differs from HEAD (`git commit --quiet -m <message>`); otherwise `local.status='unchanged'` and no commit object is created.
6. Normal push `git push --quiet <remote> refs/heads/<branch>:refs/heads/<branch>` (no `--force`, no auto-fetch/merge). The push runs even when there was nothing new to commit, so a previously rejected/pending commit is retried by the next run.
7. Verifies with `git ls-remote <remote> refs/heads/<branch>`; success is reported only when the remote commit equals the local commit. `published` means the remote ref moved, `unchanged` means it already pointed there.
8. Divergent/rejected push → `local.status='committed'`, `remote.status='failed'`, `remote.reason` contains Git's rejection (e.g. `non-fast-forward`), `remote.commit` reports what the remote actually has. Local commit and file bytes are preserved; nothing is forced or discarded. Returns the structured result instead of raising.

`ValueError` = invalid input / wrong branch / unrelated staged files (nothing mutated beyond the pre-check reads). `RuntimeError` = a Git command genuinely failed (fetch of a missing ref, `git add` of an unknown pathspec, missing `git` binary) with a sanitized message. No fallback path swaps in another transport.

Secret hygiene: every error string and `remote_url` passes `sanitize()`, which rewrites `scheme://userinfo@` to `scheme://***@`. Verified with credential-bearing HTTPS URLs (inspect output and failed fetch), and the test also asserts the password never appears.

## Integration notes for the coordinator (D02/C01)

- Compare, don't merge: `fetch_remote` → `read_remote_files(commit, managed_paths)` gives remote bytes; local bytes come from the workspace/Data layer; `local/remote` from `publish` feed the receipt's independent Git result (spec "Git publication SHALL be reported independently from local reception").
- `remote.status='failed'` with `local.status='committed'` is the spec's "remote publication fails" case: report local completion plus unpublished changes; do not reset, re-fetch-and-merge, or force.
- `missing` entries are transport incompleteness, not deletions — the receiver must retain the existing entity.
- The receipt status/exit-code mapping (`success/partial/conflict/failed`, 0/2/3/4) belongs to the CLI package (2.7/2.9); this module returns structured facts only.
- A rejected unrelated staged index is a user-recoverable refusal: surface the listed paths, do not auto-unstage.

## Design/contract observations (non-blocking, no canonical docs edited)

- `design.md` §CLI/Git定时 says "拉取到可比较 checkout" (fetch into a comparable checkout). I implemented a comparable read (private ref + `read_remote_files`) instead of materializing a second worktree, because a checkout would risk touching the user's tree/refs; the observable guarantee (remote commit and file bytes available for comparison without destructive local moves) is met. Flagging for the coordinator in case the design wording should be reconciled in FILE_CONTRACT when the receipt schema is registered.
- Unspecified by the brief: commit hooks and `commit.gpgsign` are honored from the user's git config (a signing passphrase prompt would block a scheduled run — `GIT_TERMINAL_PROMPT=0` does not cover GPG). If hourly scheduling must never block, the schedule layer needs a decision on this; I did not silently override user config.
- No timeout is imposed on fetch/push; `GIT_TERMINAL_PROMPT=0` prevents credential prompts, but an unresponsive remote can still stall a scheduled run.
- Managed-path comparison is case-sensitive; a Windows index spelling (`Notes.md`) that differs from the manifest spelling is reported as unrelated/lenient per Git's own resolution. Paths are expected to come from the exchange manifest verbatim.
- Only bytes are transported. Git's executable bit is preserved inside Git but `read_remote_files` returns content only; managed course assets are regular files, and non-regular entries are rejected loudly rather than read incorrectly.

## Remaining work (not mine)

- CLI registration, receipt/exit-code composition, coordinator file exchange (2.3/2.4/2.7/2.10) and hourly schedule acceptance (2.9).
- Full repo check + independent acceptance (3.3/3.5). Task 2.8 checkboxes were deliberately left untouched.
