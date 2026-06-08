# Gate: Red Lines — Core Prohibitions

<!-- Intermediate path convention: intermediate/{course}-{ch}/{view}/{layer}/ -->

This gate enforces the non-negotiable identity rules of lesson-kit outputs.
It applies to ALL views (first-pass, problem-set, lesson, and future views).

## Checks

| # | Failure | Return To | Forbidden Repair |
|---|---------|-----------|-----------------|
| 1 | Artifact replaces source reading — student can understand the chapter without opening the source | 03_plans | Add more quick_absorption text to make it "more complete" |
| 2 | Contains chapter summaries, mini-lessons, full explanations, or long answer explanations | 03_plans | Add detail to reduce ambiguity |
| 3 | `kp_id`, `knowledge_type`, `source_location`, `writing_view`, `rendering_intent`, `question_target`, `answer_block` metadata visible in student-facing artifact | 03_plans | Rename fields to hide them (e.g., rename `kp_id` to `编号`) |
| 4 | Workflow terminology present: 首读, 回看, 先确认, 不要急着, 记住, 这里的阅读重点是, or any phrase addressing the student as a workflow reader rather than a knowledge reader | 03_plans | Replace banned terms with synonyms |
| 5 | Exam-prep framing present: 解题入口, 本题考查, 答题模板, 得分点, 高频考点, 秒杀技巧, 题型套路, 考点归纳, or similar variants | 03_plans | Rephrase as neutral learning guidance |
| 6 | Fixed-column template rendering for every KP — artifact reads as a filled-in form rather than natural knowledge organization | 03_plans | Apply a different template without addressing the structural formalism |
| 7 | Checkpoint questions require calculation, proof, code writing, or real operation (Stage 1 only) | 03_plans | Change question target without changing question form |
| 8 | Learning-session layer present: time-boxed cards, progress logs, timed routes, 30-60 minute cards | 01_inputs | Delete the section |
| 9 | Structural drift — after removing banned words, the structure still reads as exam prep or template | 03_plans | Rearrange sections without changing structure |
| 10 | Artifact organized as exam-point summaries, drill sheets, or answer routines | 03_plans | Add prose introduction to soften the exam-like structure |

## Pass Condition

Pass only when the artifact reads as independent knowledge organization indistinguishable from a well-designed study guide. The student should feel they are reading a knowledgeable peer's notes — not a template output, not exam prep, not a workflow instruction sheet.

## Related

- `RED_LINES.md` (root) — full red line definitions
- `STYLE.md` (root) — writing style rules
- `style-and-tone.md` — complementary gate for prose quality
- `no-summary-substitution.md` — complementary gate for source-dependency
