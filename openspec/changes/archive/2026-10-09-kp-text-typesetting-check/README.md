# kp-text-typesetting-check

A **record**, not an implementation. This change specifies a read-only
typesetting check for knowledge-point bodies and queues it for a follow-up; it
writes no code.

| file | what it holds |
|---|---|
| `proposal.md` | Why the check exists, what it does and does not do, capability ownership |
| `design.md` | The measurement, its calibration, reproduction commands, wording discipline, limitations, and the measurement errors found while preparing this |
| `tasks.md` | The implementation queue for whoever builds it |
| `specs/workbench-content-governance/spec.md` | The requirement itself |

## What it is

A knowledge point's `body` is read as paragraphs separated by blank lines and
measured in **visible characters** — inline math (`$$…$$`, `$…$`) and backticked
code removed for counting, nothing else, and the stored text never touched. A
knowledge point is reported when any body paragraph falls outside **40 to 300
visible characters**.

It is not a gate. `docs/GLOSSARY.md` defines 门禁/Gate as a check that rejects the
batch on failure; this one never rejects, never rewrites text, and never says
what to typeset. Not triggering it means nothing is wrong.

## Why now

`pipeline/commands/extract-chapter.md:102` already requires blank-line separation
and forbids compressing multi-level content into one line; `:107` lists it as a
workflow Blocker. Nothing checks it. `ncmc` has a knowledge point of 7439
characters in 7 lines, each line an unbroken 1212–3584 characters;
`c04` and `dmath` are close to the convention by comparison.

## Two things this change is honest about

- The lower bound fires on 72.8% of `c04` and 83.9% of `dmath` knowledge points,
  both otherwise well-typeset. That is the accepted cost of an advisory check,
  and it is why the report prints the rarer over-long findings first.
- Repairing the existing `ncmc` bodies through the documented path needs
  `--upsert`, which resets most of a row. See `proposal.md` → Impact, and
  `tasks.md` §6. That repair is course work and waits on a different change.
