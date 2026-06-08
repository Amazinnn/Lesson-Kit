# Gate: MCQ Quality — Scene-Judgment Questions

<!-- Intermediate path convention: intermediate/{course}-{ch}/{view}/{layer}/ -->

Validates that every checkpoint question in the first-pass artifact is a genuine
scene-judgment MCQ that requires source consultation — not a definition recall,
calculation, or exam-drill question.

## Checks

| # | Failure | Return To | Forbidden Repair |
|---|---------|-----------|-----------------|
| 1 | MCQ tests definition recall or formula recognition instead of scene judgment — student only needs to remember "what is X" | 03_plans | Add "suppose you encounter a situation where..." prefix without changing question logic |
| 2 | MCQ answerable from `quick_absorption` text alone without consulting the source material | 03_plans | Make the question harder while keeping the same stem |
| 3 | Options are not homogeneous — they mix different dimensions (one about timing, one about formula value, one about circuit name) | 03_plans | Reword options without fixing the underlying dimension mismatch |
| 4 | Options are not mutually exclusive — two or more options could both be logically correct under some interpretation | 03_plans | Add "always" or "never" to force exclusivity |
| 5 | Not exactly 4 options — fewer or more than A/B/C/D | 03_plans | Add a dummy "none of the above" or "all of the above" option |
| 6 | Wrong options are straw-man distractors — obviously wrong to anyone who read the section title, not based on common misconceptions | 03_plans | Make one distractor slightly more plausible |
| 7 | Question requires calculation, algebraic derivation, proof, code writing, or hands-on operation | 03_plans | Rephrase as "which approach/formula/condition would you use?" |
| 8 | Answer explanation exceeds one sentence or becomes a mini-lesson teaching the concept | 03_plans | Truncate without preserving the judgment basis |
| 9 | Exam-prep language in question stem or options: 解题入口, 本题考查, 题型套路, 得分点, 秒杀技巧, 高频考点 | 03_plans | Replace with neutral terms |
| 10 | Question stem embeds option-distinguishing information (e.g., "which of the following Boolean theorems, unlike DeMorgan's law...") — the stem itself narrows the options | 03_plans | Remove the distinguishing hint from the stem |

## Scene-Judgment Self-Check (Agent must verify before submitting)

1. **Source-dependency test:** Can this question be answered correctly by reading ONLY the `quick_absorption` text? If YES → FAIL.
2. **Misconception test:** Does each distractor represent a real, documented common error for this knowledge type? If NO → FAIL.
3. **Locatability test:** Does the correct answer require the student to locate a specific passage, figure, table, or formula in the source? If NO → FAIL.

## Pass Condition

Pass only when EVERY MCQ is a genuine scene-judgment question with 4 homogeneous, mutually exclusive options, each requiring source consultation to answer. Zero definition-recall, zero calculation, zero exam-prep language.

## Related

- `scene-judgment-mcq.md` skill — how to design these questions
- `no-summary-substitution.md` gate — complementary check for source-dependency
- `style-and-tone.md` gate — complementary check for exam-prep language
