# 2026-08-16 Frontend Phase 2 (final): P1 logic fixes + DSH visual alignment + cleanup

Per `docs/frontend-optimization-plan.md` (v3.1), the consolidated final phase. All four user decisions applied: B6.10 tokens updated to measured DSH values; AI recent-problems feeding deferred (copy fixed); auto-grade marked deferred in spec; AI column collapse defaults to expanded with remembered state.

## P1 logic / contract fixes
- KP detail page: KaTeX now renders server-rendered math spans on load (`renderMath(#middle)` in page init).
- Rating confirmation message is honest per action (rated → 评分已入库；stuck → 卡点已标记；skip/unrated → 未反馈).
- Session-end list shows only truly unrated items (`state === "unrated"`); no double rating.
- 再练同类 clears the session queue first (new-session semantics, no instant 已练完).
0
- **AI tasks are now asynchronous** (`api.py ai_run`): the provider run happens on a worker thread with its own Pool (sqlite is not thread-shareable); the HTTP response returns a real job id within ~ms (bounded wait for the job record + status.json). POST /ai/explain went from up to 300 s (provider timeout) to ~15 ms. Unknown problem ids return 404 (ApiError) instead of a raw 500; `app.py` also maps FileNotFoundError → 404 so the poller's 404-tolerant path covers the record-not-yet-visible race.
NaN
NaN
NaN
0
NaN
NaN
NaN
NaN
NaN
NaN
NaN
0
NaN
NaN
0
NaN
NaN
NaN
0
NaN
NaN
NaN
NaN
NaN
0
NaN
NaN