# rating-toggle-setting

A left-rail settings section whose first entry turns self-rating off entirely —
and a verdict-derived learning state for the rounds that do.

| file | what it holds |
|---|---|
| `proposal.md` | Why rating cannot be escaped today, and what the toggle changes |
| `design.md` | `"off"` end-to-end, why no synthetic rating events, why localStorage |
| `tasks.md` | What was touched |
| `specs/workbench-ui/spec.md` | MODIFIED per-problem rating + ADDED learner settings |
| `specs/review-workbench/spec.md` | MODIFIED practice session (optional rating, verdict-derived conclusions) |

## What it is

Self-rating is the only way forward in per-problem mode and the only writer of
learning state. Both are now optional, together:

- **左栏「设置」**：one checkbox, 「练习与组卷显示自评」, default on = today's
  behavior, stored in `localStorage` per workspace (survives tabs and restarts).
- **Off = invisible**: no rating-timing fieldset, no feedback panel, no
  session-end detour, no rating label in records. A saved paper starts with
  `rating_mode: "off"`.
- **Off flow**: submit → verdict (+ correct option highlight) → 查看解析 →
  「下一题」 advances. Nothing auto-advances; the learner reads the solution
  first. Flash cards become pure browsing through the existing card paging.
- **Verdict-derived conclusions**: in an off round, an objective verdict writes
  progress, current state, and schedule (对 → mastered, 错 → wrong; skip still
  marks stuck). No `feedback_events` row with a rating is written, so 平均自评
  and the 1–5 distribution stay free of synthesized data.

Plus the bug this started from: an empty rating input passed the client bounds
check (`parseInt("")` is NaN) and died server-side as "rating or note is
required", trapping the round.

## What is not here

A server-side preference store, changes to the agent attempt contract, any
change to immediate/batch rounds, verdict-derived state for subjective
problems.
