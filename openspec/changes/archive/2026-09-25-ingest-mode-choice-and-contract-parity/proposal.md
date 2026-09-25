## Why

Two defects keep the learner from getting their content in, and both were
observed live on 2026-09-25 (chapters 18–22 of a physics course, 509 objective
questions of a data-structures course):

1. **The Agent reports that a turn can only carry one chapter.** Its words: 「一批的
   id 前缀由该批的章节决定，所以一批只能属于一章，而一轮又只受理一个批次——这是入库
   契约本身的结构」. The mechanism for multi-chapter turns exists (one manifest may
   span chapters, every content block of a reply is applied, one batch per
   chapter), but three things let the Agent conclude otherwise:
   - a natural **inline** manifest `{"type": "content-bundle", …}` is refused
     because only `kind` is accepted, while the prompt says inline manifests are
     allowed without showing the shape;
   - the prompt promises that a chapter-less item falls back to the workspace
     chapter, and the gate refuses it instead (`_gate_content_bundle`'s `chapter`
     argument is dead: no caller passes it). An Agent that hits the refusal
     concludes that a batch must be pinned to exactly one chapter;
   - the success/rejection wording talks about 「整批」 and 「按章各记一个批次」
     without stating that the prevalidation, backup, and transaction cover the
     whole manifest, so "one manifest = one batch" reads as the rule.
2. **An objective question without an answer key cannot be imported as an
   objective question.** Their question banks are mostly 判断题/单选题, and the
   exports lost the correct answers; micro items require `answer_key`, so the
   gate refused them and the Agent fell back to importing all 509 as plain
   `problem_type: other` problems — which are **exam-only** (`practice_modes`
   NULL), leaving the 判断 and 小测 modes empty for both courses (verified:
   c01 123/123 and c02 683/683 rows are `practice_modes NULL`, `micro_quiz NULL`).

The learner's decision: keep importing objective items **without** a key
(self-assessed, no automatic grading), be able to fill keys in later, and
re-import both courses once this works.

## What Changes

- **A keyless objective item is a first-class import.** `answer_key` may be
  omitted or `null`; `yes_no` still needs `options` (default 是/否) and the
  choice types still need 2–6 `options`. `error_reason` stays mandatory when a
  key is present and becomes optional when it is absent. The batch result and
  the next-turn context report how many items came in without a key.
- **The practice page stops pretending.** A micro item without a key is not
  graded (today the comparison against a null key marks every answer wrong and
  prints an empty 答案): the item shows 「本题未录入答案键，请对照课本/解析自评」,
  keeps the choice layout, and the existing 1–5 rating still drives the learning
  state.
- **A key can be filled in later** through `lesson-kit data update problem`
  (`answer_key`, validated against the item's own quiz type; clearing it returns
  the item to keyless) — so the Agent or the learner can complete keys whenever
  the source provides them.
- **The contract and the code agree.** An inline `content-bundle` block is
  accepted with either `kind` or `type`; the chapter rule is stated as it is
  implemented (item → bundle → refused, never the workspace chapter, so a
  multi-chapter manifest cannot be silently mislabeled); the prompt carries a
  contract version line and states plainly that one reply may carry several
  chapters and several blocks, that a plain problem declaring a micro/yes-no
  mode is refused with the exact fix, and that 综合题/判断/小测 are selected by
  the fields (`problem_type` is the subject-matter form, not the practice mode).
- **A reply that stops early is corrected in the next turn**: after a successful
  import the next-turn context says to continue the remaining chapters directly
  instead of asking the learner for another 「继续」.

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`: the content action contract (inline shape, chapter rule,
  multi-chapter/multi-block continuation, contract version) and the outcome
  notice.
- `micro-quiz-content`: the micro-quiz content contract (keyless items) and
  type-aware rendering (no verdict without a key).
- `workbench-content-governance`: the staged bundle's chapter rule.
- `review-workbench`: the practice page's rendering of an ungraded objective item.

## Impact

`workbench/bridge/conversations.py` (prompt, action resolution, notices),
`workbench/ingest/__init__.py` (gate, chapter rule, keyless counting),
`workbench/domain/micro_quiz.py` (keyless validation), `workbench/data/content.py`
(`answer_key` editing), `workbench/server/static/workbench.js` (ungraded rendering,
duplicate result card), docs (prompt, GLOSSARY, PRODUCT-MANUAL, REQUIREMENTS,
ACTION-GRAPH, FILE_CONTRACT). No pool schema change, no new user-facing noun, and
no automatic writes: the existing 806 problems stay exam-only until the learner
re-imports them.
