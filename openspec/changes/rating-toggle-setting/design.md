# Design notes

## `"off"` is a real rating mode, not a client-side mime

The alternative — store `immediate`/`batch` in the pool and have the browser
hide the panels — would make `practice_runs` lie about what happened, and the
resume-reload path (which redirects ended batch rounds to session-end) would
need client-side state to second-guess the stored mode. One honest value
threads through every checkpoint for free: the start bodies, the
`active_practice` row, the archived run, the records label (关闭自评), the
resume redirect (which keys off the stored mode already). The server treats it
like the other two values: a non-empty string, validated into the same set.

The setting's effect is pinned at round start (the stored mode is), so flipping
the checkbox mid-round changes the next round, not the running one — the same
rule as every other per-round choice.

## Verdict-derived state writes progress, not rating events

`feedback.apply` already maps 1–5 to statuses (`RATING_PROGRESS`: 1–2 wrong,
3 reviewing, 4–5 mastered) and moves progress, current state, and schedule. An
off-round verdict maps onto the same statuses directly (对 → mastered,
错 → wrong) in `record_browser_attempt`, reusing `schedule_rules.after_result`
with those status words the way the stuck path already does.

The deliberate omission is the `feedback_events` row. Every rating lands there,
and the records center aggregates it into 平均自评 and the 1–5 distribution —
a synthesized 5/2 per answer would fabricate self-assessments the learner never
made. The attempt row already carries the verdict (客观题正确率 reads it), and
the learner signal notes path is untouched. Nothing in the stats pages needs a
change: an off round simply has no ratings to average.

## Why the off flow ends with a click, not a timer

The batch mode auto-advances 2s after a verdict because its rating happens
later at session-end. The off learner advances *after reading the solution* —
an unbounded read time a timer cannot guess. So off reuses per-problem mode's
explicit-action shape: submit (verdict renders), 查看解析 when wanted, then
「下一题」. The button appears only once the item is answered, in the same
composer row as 查看解析; `advance()` alone — the attempt was already written
at submit, so there is nothing to save.

Flash cards have no verdict to derive from and no answer-submit step; their
existing card navigation (`#card-nav`) already pages without any write, so off
just never reveals the rating panel. An off card round produces no learning
records — browsing is not studying.

## localStorage, and the one precedent it sets

Every existing client state lives in `sessionStorage` on purpose: selections,
filters, folds — states a click re-creates. A preference is different: it should
hold without the learner re-stating it every tab. The workbench is single-user
and local; a server-side store would add a route, a file module, and locking
for one boolean. `localStorage` under `wb_settings_<ws>` (JSON, same shape as
the session store) is the whole mechanism. The glossary records the new
precedent and its one rule: preferences only.

## The empty-rating trap

`parseInt("")` is `NaN`; `NaN < 1` and `NaN > 5` are both false, so the inline
guard passed and the empty value reached the server, which rejected it as
`rating or note is required` — far from the input, looking like a stuck round.
Both guards (per-problem and session-end) now reject anything outside 1–5
including NaN: `!(rating >= 1 && rating <= 5)`.

## Verification

Off-card forward navigation uses the existing PATCH current-practice checkpoint:
answered after reveal, stuck for explicit skip, with no synthetic rating or
learning projection. The final item archives the execution snapshot. Display,
reveal and backwards review do not settle a pending item.

- JS: an off round posts `rating_mode: "off"`, starts without choosing a
  timing, never shows the feedback area, shows 「下一题」 after submit and
  advances on click; flash cards page without rating surfaces; the setting
  round-trips through localStorage; an empty rating is rejected inline.
- Python: `"off"` accepted by both start routes and labeled 关闭自评 in
  records; an off-round verdict writes progress/current-state/schedule and no
  rated feedback event; the settings section renders on every page.
- `pytest tests -q`, `node --test tests/workbench/*.test.js`,
  `openspec validate --strict`, daemon restart, live round on a real paper.
