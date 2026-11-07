# Implementation checkpoint

Source branch `codex/course-sync`, based on `c5a9c642`. Isolated source root `D:/.codex/worktrees/course-sync/lesson-kit`. Main checkout and real course data remain separate.

## Completed focused unit

Pure `plan_exchange` comparison and nine targeted regression checks. The initial collection failed with ModuleNotFoundError. After implementation `python -m pytest tests/workbench/test_course_sync.py -q` reports 9 passed. Checks cover one-sided additions/updates, equal convergence, conflicts, deletion vs edits, missing assets, source-identity history union, per-question drafts, transitive invalid dependencies, valid dependency cycles and referenced deletion. This is focused verification, not package acceptance.

## Worker execution

DeepSeek Harness `0.1.5-rc.1`, provider `opencode-go`, model `deepseek-v4.1-flash`. Separate per-run overlays and session headers, no credential values in project files. P00 read AGENTS, executed a shell command, and wrote a probe JSON. D01/I01 failed on their first request with 429 overloaded before product output and were reassigned to the coordinator. G01 Git transport and P01 preferences continue. Maximum worker concurrency is four. Provider stop-dispatch started around 11:02.

The headless entry creates a fresh persisted session, and exposes no resume flag. No claim of tested native session continuation is made. Task briefs and disk checkpoints enable explicit recovery, and SDK continuation remains to verify if needed.

## Outstanding

Full Data export/reception, cross-device integer identity mapping, per-question unfinished Paper projection, CLI registration, Git composition, hourly task, free-LLM Tutor acceptance and full real-environment acceptance are not complete. New pure comparison code is not a delivered synchronization feature.

The pre-change full pytest run is still being collected. It already contains failures before product implementation and its final summary must be recorded.
