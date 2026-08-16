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

## Post-implementation review fixes (Claude Code read-only round)

- `_send_static`: reject `..` path segments and use component-wise `is_relative_to` containment (the old string-prefix check had a sibling-directory bypass).
- `renderResult`: skip empty section titles (no more empty `<h4>` when the first chunk is a bare heading).
- AI 讲解/诊断 buttons disabled while no problem is current (DSH-style affordance), synced in `updateAiContext`.
- KP detail empty lists render a muted `—` placeholder instead of `无`.
- Not applied (verified false or design choice): KaTeX is already vendored (static/katex present); hub_stats keys are contractually present; per-workspace session queue is kept on workspace switch (aligns with the user's 巨无霸长对话 ideal); 1024px collapse breakpoint matches DSH's own SIDEBAR_AUTO_COLLAPSE constant.
