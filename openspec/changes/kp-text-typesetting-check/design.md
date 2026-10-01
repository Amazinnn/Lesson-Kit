# Design — measurement, calibration, and what the check may say

## 1. The measurement

**Paragraph.** A run of text between blank lines. Whitespace-only lines do not
start a paragraph.

**Visible characters.** A paragraph's length counted after removing, for counting
only, three inline constructs: `$$…$$`, `$…$`, and backticked code. Nothing else
is removed, and **the stored text is never altered** — the removal exists so that
one ruler works across a Chinese course, an English course and a formula-heavy
course.

Why not the alternatives:

| candidate unit | ncmc p50 | c04 p50 | dmath p50 | verdict |
|---|---|---|---|---|
| total characters | 659 | 70 | 51 | overstates `ncmc` by **1.76×** (44% of its text is LaTeX source) while overstating `c04` by 1.09× — the same number means different things per course |
| 汉字 only | 296 | 48 | 15 | meaningless for `dmath`, an English course: 15 汉字 in a 51-character paragraph |
| **visible characters** | **374** | **64** | **35** | language-neutral and proportional to what the reader sees |

The 汉字 trap is not hypothetical. `ingest-integrity-and-observability` P1-27
records a course-local validator that measured `len()` against a "汉字"
specification and passed 100/100 rows whose real CJK median was 353.

## 2. Calibration of the band, and its honest limits

The band is **40 to 300 visible characters**, both ends hard. Paragraph totals
were cross-checked against an independent run and matched exactly
(514 / 3830 / 141).

| | ncmc | c04 | dmath |
|---|---|---|---|
| knowledge points | 100 | 324 | 31 |
| paragraphs | 514 | 3830 | 141 |
| visible / total | 56% | 92% | 65% |
| visible p50 | 374 | 64 | 35 |
| visible p75 | 588 | 130 | 50 |
| visible p90 | 737 | 194 | 80 |
| visible p99 | 1750 | 293 | 248 |
| visible max | 2258 | 473 | 267 |
| bodies with a paragraph > 300 | **100%** | 8.3% | 0% |
| bodies with a paragraph < 40 | 0% | **72.8%** | **83.9%** |
| bodies triggering either | 100% | 76.5% | 83.9% |

Other fields, which is why the band is `body`-only:

| field | ncmc visible p50 / max | c04 | dmath |
|---|---|---|---|
| `learning_action` | 42 / 81 | 40 / 66 | 0 / 0 |
| `fragile` | 184 / 308 | 0 / **576** | 0 / 11 |

A 40 floor on `learning_action` would misfire on 37–49% of it; a 300 ceiling on
`fragile` would misfire on `c04`, which reaches 576.

**What the calibration is and is not.** 300 was chosen because it sits above
`c04`'s maximum paragraph (473 exceeds it, so 8.3% of `c04` bodies are reported)
and far below `ncmc`'s p90. It is a marker for departure from a distribution, not
a statement that 300 characters is correct. 40 is not derived from a measurement
at all — it marks the degenerate case of a paragraph with almost nothing in it.
Both are advisory: not triggering means nothing is wrong, and a 41-character
paragraph is as acceptable as a 300-character one.

**Known cost, accepted by the owner.** The lower bound fires on 72.8% of `c04`
and 83.9% of `dmath`, both of which are otherwise well-typeset. This is why the
report prints the over-long section first.

## 3. Sample

`ncmc-ch03-kp-006`「换元积分法与分部积分法」— 7439 characters, 7 lines:

| section label | visible characters in that section |
|---|---|
| 定义。 | 1212 |
| 成立条件与前提。 | 1325 |
| 教材例题与推导。 | 3584 |
| 本考纲里真题怎么考。 | 1273 |

The labels are already separated by blank lines — the first level of the
convention is met. Below each label the content is a single unbroken line; the
third section holds worked examples and inline formulas, which is the second
level `:102` forbids.

## 4. What the report may say

Every entry is a recomputable fact about the stored text:

- over-long section: knowledge point id, how many paragraphs are past the upper
  bound, the longest measured paragraph, the shortest measured paragraph;
- short section: knowledge point id, how many paragraphs are below the lower
  bound, the same two extremes;
- a knowledge point that violates both bounds appears **once**, in the over-long
  section, stating both counts;
- a scope with no bundle to check says so, which is distinguishable from a scope
  that was checked and found clean.

**Prohibited in the report and in any prose describing it**: a target paragraph
length, a recommended section vocabulary, a suggested split point, a template, or
any wording that tells the author how to typeset. The check says a measurement is
unusual; it does not say what to do about it.

## 5. Two points, one rule

| point | input | host | frozen-layer exception |
|---|---|---|---|
| before apply | content bundle | `workbench/ingest` | none — `AGENTS.md` sanctions new code in `workbench/` |
| after apply | pool, per chapter | `pipeline/scripts/validate-pool.py` | yes, for this one read-only check |

The post-apply host is chosen because a per-chapter pool report already runs
there and already distinguishes a WARNING from a failing gate (`:16-19`, and
`:273` for a missing `coverage-check.md`). Hosting is not ownership: the
requirement is about content quality, which `workbench-content-governance` owns.

The exception granted for this change does **not** unfreeze `pipeline/`. It does
not apply to `ingest-integrity-and-observability`'s P0-2, P0-3, or the
`candidate_contract.py` collapsed-subpart finding.

## 6. Reproduction

All read-only; the working directory is the named course's `pool/`. On Windows,
pass the python program through a single-quoted here-string and build the dollar
sign with `chr(36)`, because a double-quoted here-string interpolates `$$` and a
bare `$` is a regex anchor.

```powershell
$code = @'
import sqlite3, re, sys
D = chr(36); E = re.escape(D); BT = chr(96)
INL = re.compile(E + E + '.+?' + E + E)
INM = re.compile(E + '[^' + D + '\n]+' + E)
COD = re.compile(re.escape(BT) + '[^' + BT + '\n]+' + re.escape(BT))
def paras(t):
    return [l for l in t.replace(chr(13) + chr(10), chr(10)).split(chr(10)) if l.strip()]
def vis(l):
    return len(COD.sub('', INM.sub('', INL.sub('', l))).strip())
c = sqlite3.connect('file:' + sys.argv[1] + '?mode=ro', uri=True)
rows = [r[0] or '' for r in c.execute('select body from knowledge_points')]
allv, lo, hi = [], 0, 0
for t in rows:
    vs = [v for v in (vis(l) for l in paras(t)) if v > 0]
    allv.extend(vs)
    lo += 1 if any(v > 300 for v in vs) else 0
    hi += 1 if any(v < 40 for v in vs) else 0
A = sorted(allv)
q = lambda p: A[min(len(A) - 1, int(len(A) * p))]
print('KP', len(rows), 'paras', len(allv),
      'p50', q(.5), 'p90', q(.9), 'max', A[-1],
      'over300', lo, 'under40', hi)
'@
Set-Location 'D:\Documents\Document_In_University\竞赛\全国大学生数学竞赛\pool'
python -c $code ncmc.db
```

Expected for `ncmc`: `KP 100 paras 514 p50 374 p90 737 max 2258 over300 100 under40 0`.
For `c04`: `KP 324 paras 3830 p50 64 p90 194 max 473 over300 27 under40 236`.
For `dmath`: `KP 31 paras 141 p50 35 p90 80 max 267 over300 0 under40 26`.

The paragraph counts are the cross-check: if a run does not reproduce 514 /
3830 / 141, the measurement is wrong, not the pool.

## 7. Corrections made while measuring this

Recorded because the three failures are the same failure mode and a later
implementer will hit them:

1. A double-quoted PowerShell here-string interpolated `$$` into the regex
   source, so the math-stripping pattern became nonsense. It reported that
   stripping removed nothing.
2. A bare `$` written where a literal dollar was meant is a regex **anchor**, so
   the pattern matched nothing while looking correct in review.
3. Iterating rows as `for row in B` and then taking `row[0]` returned the first
   *character* of the body, collapsing 514 paragraphs to 98.

Each produced a tidy, plausible number. None was caught by reading the code —
only by checking the result against a known invariant (paragraph count 514, and
the sample text that visibly contains `$F(u)$`).

## 8. Known limitations

- The lower bound fires widely on well-typeset courses (§2). Accepted; the
  two-section order mitigates the reporting consequence.
- 40 and 300 are language-flavoured numbers. They mark departure, not
  correctness.
- The check reads paragraphs, so a body written as one long line with no blank
  lines at all is a single paragraph and is reported as one finding, not as the
  several units it contains. Distinguishing those needs the seam boundary, which
  is deferred.
- Seam detection is out of scope, so a course whose bodies carry no structural
  markers gets paragraph length only.
