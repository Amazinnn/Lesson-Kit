## Context

The practice page builds its reveal / rating-card HTML in
`workbench/server/static/practice-flow.js` along two branches: the exam flow
renders the problem's `solution` through an explanation section (section
kicker labelled by `solution_origin`, "本题无解析" when empty), while the
micro-quiz branch stopped at answer key + `error_reason` because the spec
required cards to show the key "instead of a formal solution". The data
already exists on the row: 494/497 pool problems have a 250+ character
`solution`. See proposal.md — Why.

## Goals / Non-Goals

**Goals:**

- Make the stored `solution` visible on micro-quiz reveal and session-end
  rating cards, with the same section markup and origin label the exam flow
  already uses.
- Keep every other micro-quiz behavior byte-identical: verdict logic,
  keyless notice, rating flow, learning writes, unified-mode hold.

**Non-Goals:**

- No pool/data repair: the 109 keyless items, 3 empty `solution` items, and
  437 sub-40-character `error_reason` strings stay as they are.
- No new answer surface: `source_answer` (ingest file-path evidence) is not
  appended under a learner-facing "教材答案" heading in the quiz branch.
- No server/API/pool schema change; no change to exam-flow rendering.

## Decisions

- **One shared renderer, two call sites.** A single
  `practiceExplanationSection(problem)` helper is called from both quiz
  branches (per-item reveal and batch/off-mode rating card) and is reused
  verbatim by `practiceSolutionHtml`. Alternative considered: duplicating the
  section markup per branch — rejected, the original drift (exam showed
  `solution`, quiz did not) is exactly this duplication.
- **Label by `solution_origin`, generic fallback `解析`.** Same mapping as
  the exam flow, so an item looks identical whichever mode pulled it.
  Alternative: a quiz-specific heading — rejected, it would reintroduce
  mode-dependent presentation of the same field.
- **Empty `solution` returns `""` (no empty section).** The quiz branch
  relies on `+`-concatenated HTML fragments; returning a placeholder would
  add a visible empty block for the 3 solution-less items. The exam flow
  keeps its "本题无解析" fallback for backward compatibility.

## Risks / Trade-offs

- [Long solutions lengthen rating cards] — mitigated: the exam flow already
  renders these same strings on its cards; no new rendering surface or size
  class is introduced.
- [Spec delta vs. implemented text drift] — mitigated: the delta was copied
  from `openspec/specs/micro-quiz-content/spec.md` in full and edited in
  place, then validated with `openspec validate`.
- [Reward-card reading load increases] — accepted trade-off: the learner
  explicitly asked for the detail behind the one-line error reason.

## Migration Plan

Pure front-end file change; ships with the normal workbench static-asset
serving, no rollout order. Rollback = revert `practice-flow.js` (old behavior
is spec-compliant under the pre-change requirement).

## Open Questions

None — scope decisions (UI-only, no data backfill, no `source_answer` block)
were confirmed with the user before implementation.
