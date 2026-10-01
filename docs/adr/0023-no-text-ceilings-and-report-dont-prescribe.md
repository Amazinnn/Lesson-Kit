# ADR 0023: No text length ceilings, no scripted text rewriting, and checks that report rather than prescribe

## Status

Accepted (2026-10-01).

## Context

Two course-ingest jobs — `ncmc` (全国大学生数学竞赛) and `c04` (宏观经济学（甲）) —
produced knowledge-point bodies that are hard to read: one `ncmc` body is 7439
characters across 7 lines, each line an unbroken run of 1212–3584 characters.

The instinct on seeing that is to add a length ceiling. This repository has
already tried that twice and reversed it twice:

- **`micro_quiz.py:8-10`**, in code: "No stem length bound: a question bank's
  判断题/单选题 are as long as the source paper makes them … and refusing them by
  length sent real objective items into the exam shell."
- **D9** in `content-dedup-and-audit/design.md:126-138`, which removed
  `MAX_STEM_CHARS` outright: "Length is not an answering-form property … the
  author's own note on the constant already said it was a ceiling, 'not a design
  statement'."

The ADS repair behind D9 found 14 objective rows over the bound, seven of them
long multi-assertion items whose options were inlined in the stem. The bound was
the single reason real 判断题/单选题 sat in 综合题. Raising it to 1300 was
considered and rejected: any finite number repeats the same failure on the next
paper that is slightly longer.

A second instinct is to write a script that fixes the text — re-splitting the
long lines, normalizing the markup, trimming. That was ruled out for a reason
that does not scale: **a script cannot adapt to the variety of language.** The
same three pools that motivated this record carry three different section
vocabularies (ncmc: 定义。/成立条件与前提。/教材例题与推导。/本考纲里真题怎么考。;
c04: 考试怎么用/应用/定义/易错点/…; dmath: no shared vocabulary at all, only
English theorem fragments). There is no correct target for a script to converge
on.

## Decision

1. **No length ceiling is placed on stored text.** Not on knowledge-point bodies,
   not on stems, not on any content field. A ceiling is a refusal rule wearing a
   measurement's clothes, and this repository has twice paid for it diverting
   real content into a fallback path.

2. **No script rewrites content text.** No automatic re-splitting, reflowing,
   trimming, normalizing or reordering. Text is corrected by writing it again.
   Read-only analysis is not rewriting: a check may measure, count, and report.

3. **Checks about text report; they do not prescribe.** A check states a
   measurement is unusual. It does not state a target length, a recommended
   section vocabulary, a suggested split point, or a template. The owner is
   explicit that this is a reminder, not a requirement: if the check does not
   fire, nothing is wrong, and 41 characters is as acceptable as 300.

The consequence for naming follows from (3): because these checks never refuse,
they are **not 门禁 / Gate**, which `docs/GLOSSARY.md` defines as a check that
rejects the whole batch on failure. They are 排版检出 / typesetting check. The
existing definition is left intact; the new thing gets its own name.

## Consequences

- Readability is a property of the writing and of the rendering, not of a
  constraint on the data. A course that wants shorter bodies gets them by
  writing them shorter.
- Findings are noisy by design. The typesetting check in
  `kp-text-typesetting-check` fires on 72.8% of `c04` and 83.9% of `dmath`
  knowledge points, both of which are otherwise well-typeset. That is accepted:
  an advisory check that never blocks may over-report, and a reader who finds a
  finding uninteresting dismisses it.
- Because the check never blocks, a finding can be ignored indefinitely without
  any machinery noticing. That is the accepted trade: the alternative is a gate,
  which is what this ADR rules out.
- An Agent reading this ADR should not add a `MAX_*_CHARS` for any content field.
  If a bound seems necessary, the question to ask is whether the content is being
  routed into a fallback path, which is what the previous two bounds caused.
- A future check that *does* need to refuse is a different kind of thing and may
  legitimately be a 门禁; this ADR does not restrict that.
