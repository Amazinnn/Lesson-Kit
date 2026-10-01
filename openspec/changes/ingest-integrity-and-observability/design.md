# Design — defect ledger

## What this file is

The evidence behind `proposal.md`. Every row cites either a `file:line` that was
read in the current tree, or a read-only query whose result is reproduced in
[Reproduction](#reproduction). Anything a single sweep reported but nobody
re-ran is marked **unverified** and is not counted as a commitment.

Two course-ingest jobs produced this ledger:

| course | workspace | pool | material | window |
|---|---|---|---|---|
| `ncmc` 全国大学生数学竞赛 | `D:\Documents\Document_In_University\竞赛\全国大学生数学竞赛` | `pool/ncmc.db` | 17 papers (2009–2025) + textbook, 8 chapters | 2026-09-28 → 2026-10-01 |
| `c04` 宏观经济学（甲） | `D:\Documents\Document_In_University\课程\2026-2027 秋冬 大二上\宏观经济学（甲）` | `pool/c04.db` | 8 textbook chapters + 16 past-paper batches | 2026-09-30 → 2026-10-01 |

Paths below are written `ncmc:…` / `c04:…` for workspace files and
`repo:…` for files in this repository.

## Method and its limits

- Four read-only sweeps covered the workspaces: the `ncmc` audit reports, the
  `ncmc` hand-written tooling, the `c04` problem-repair tooling, and the `c04`
  knowledge-point / ingest / cross-link tooling.
- Every `repo:` claim in this file was re-read at the cited line in the current
  tree. None of them come from a sweep report.
- Every pool number in [Independently recomputed](#independently-recomputed) was
  re-run by the recorder against the live pool in read-only mode. Where a sweep
  number could not be reproduced, it is marked unverified rather than dropped
  silently.
- Sweeps were given a hypothesis to test, not a conclusion to confirm. One
  hypothesis was refuted; see [Refuted](#refuted-hypothesis).

---

## Route per item

How each item below must be fixed. `proposal.md` and `tasks.md` use the same
four labels.

| # | route | why |
|---|---|---|
| P0-1 | `NEW-GAP` | Stable ids: no requirement exists. Highest value, needs its own change. |
| P0-2, P0-3, P1-2 | `DOCTRINE` | All three are in `pipeline/`, frozen by `AGENTS.md:38-39` and carved out of scope by `openspec/changes/archive/2026-09-20-optional-problem-difficulty-gate/specs/workbench-content-governance/spec.md:13-14`. |
| P0-4 | `NEW-GAP` | No cross-reference gate for problems ↔ knowledge points. The flash-card equivalent already exists (`openspec/specs/flash-card/spec.md:19-20,37`) but is not applied here. |
| P1-1 | `NEW-GAP` | `difficulty` coverage: the spec deliberately promises nothing (`openspec/specs/problem-difficulty/spec.md:77-80,87-90`); only the code docstring overclaims. |
| P1-12 | `CONFORMANCE` | "every inserted row carries the batch id" (`openspec/specs/workbench-content-governance/spec.md:163`, scenario `:167-168`). 100% NULL violates a live SHALL. |
| P1-10 | `NEW-GAP` | The apply path has no requirement that reported accounting match reality. "the reported accounting matches the recorded counts" exists only at `:173`, inside the *Roll back a whole batch* scenario — and it compares the reported figure against the recorded one, both derived from the same record, so a constant count satisfies it. |
| P1-11 | `NEW-GAP` | A backup path is required (`:163`) but distinct per-batch files are not. |
| P1-18 | `CONFORMANCE` | `workbench-ui` already requires one consistent, escaped-then-rendered math pipeline (`openspec/specs/workbench-ui/spec.md:1077-1083,1090-1093`); the server path escapes twice. |
| P1-19, P1-20, P1-21, P1-22 | `NEW-GAP` | Graph label / search / filter semantics: no requirement defines them. |
| P1-23, P1-24 | `NEW-GAP` | No formula validator; textbook import does no entity or heading normalisation. |
| P1-25, P1-26, P1-27, P1-28 | `NEW-GAP` | Undocumented contracts — `FILE_CONTRACT.md` mentions none of `source_location`, `related_kp_ids`, `fragile`, `graph_label`. |
| P1-3 … P1-9, P1-13 … P1-17 | `NEW-GAP` | Manifest schema, cross-chapter relations, dedup fingerprint, difficulty provenance, ledger coverage. |
| P2-29 … P2-36 | `NEW-GAP` | Missing read/query, dry-run, two-phase commit and logging affordances. |
| — | `NOT-A-DEFECT` | See [Not defects](#not-defects-recorded-so-they-are-not-fixed). |

## Not defects — recorded so they are not "fixed"

`knowledge_relations` stays empty and edge direction stays discarded. Both were
reported by the first sweep as defects. Both are what the spec requires:
"Edges originate only from formal relations **or existing `related_kp_ids`**"
(`openspec/specs/review-workbench/spec.md:347-348`) permits the empty table, and
"WHEN two knowledge points declare duplicate or reverse semantic relations THEN
the graph model returns one edge for the **unordered pair**" (`:355-358`)
mandates the direction loss. An earlier draft of this change would have proposed
breaking a live requirement.

---

## P0 — data is wrong or was wrong, and nothing reported it

### P0-1 · `problem_id` is minted by position, so a rebuild renumbers the survivors — `NEW-GAP`

`c04` lost 37 problems to a concurrent dedup and rebuilt its manifests from the
surviving shard specs. Problem ids are minted by a positional counter
(`c04:intermediate/c04/problem_extraction/b01/_build/build.py:98-103`), so a rebuild
re-mints them from position rather than from identity.

A 974-row pre-deletion snapshot of the pool exists, in
`c04:pool/backups/c04-before-spacingfix-20261001-003817.db` (and
`c04-prerebuild-20261001-064216.db`, also 974). Diffing it against the live pool on
`problem_id` and comparing normalized question text:

```
current pool: 937 problems
against c04-before-spacingfix (974 rows):
  deleted ids   37    ch01 1, ch02 3, ch03 0, ch04 2, ch05 3, ch06 2, ch07 10, ch08 16
  added ids      0
  common ids   937
    same question      512
    DIFFERENT question 425     <-- displaced
example: c04-ch01-prob-204
  before  新古典增长模型中储蓄率变化的影响。
  after   用数理方法和几何方法推导BP曲线,说明其经济含义,分别画出……
```

**425 of 937 problem ids now denote a different question.** Per chapter the
displaced counts are ch01 6, ch02 124, ch03 0, ch04 35, ch05 25, ch06 89, ch07 48,
ch08 98; ch03 is zero because it lost no rows.

An earlier draft of this change argued the displacement from the *absence of gaps*
in the live id sequence. That argument is circular and has been removed: the
974-row snapshot is **also** contiguous `1..N` in all eight chapters, so
contiguity describes the before state as well as the after one and says nothing
about renumbering. The snapshot diff is the evidence.

Consequence: any id-keyed artefact predating the rebuild silently retargets. The
repair scripts discovered this the hard way and had to re-locate 23 problems by
content signature instead of by id (`refix.py:31-33`). Nothing in the toolchain
can detect it: `knowledge_points` and `problems` both key on these strings, and
`problem_attempts` / `problem_progress` / `review_schedule` key on them too.
`c04` has no learning records yet, so nothing is corrupted *there* today; the
same run on a course that has been practised would attach history to the wrong
questions.

Note for anyone re-deriving this: the shard-level backups under
`problem_extraction/_fixtool/_backup/` are **post**-deletion and yield a
displacement of 0. Only the pool-level snapshots in `pool/backups/` show it. The
manifest-level backup was likewise taken after the deletion and is byte-identical
to the post-deletion manifest in all 8 batches (`apply_final.py:19,123-124` copies
only when the target is absent; `_backup` and `_backup_clean` hash equal).

### P0-2 · `--upsert` rebuilds the row from the manifest and NULLs every other column — `DOCTRINE`

```
repo:pipeline/scripts/insert-problems.py:256-259
    "INSERT OR REPLACE INTO problems "
    "(problem_id, kp_ids, problem_text, solution, problem_type, source_kind) "
repo:pipeline/scripts/insert-knowledge-points.py:254-259
    "INSERT OR REPLACE INTO knowledge_points "
    "(kp_id, knowledge_item, graph_label, source_location, knowledge_type, "
    "related_kp_ids, importance, learning_action, body, difficulty, fragile) "
```

`INSERT OR REPLACE` deletes the conflicting row and inserts the new one, so any
column absent from the manifest returns to its default. On the problem side that
is `exam_year`, `difficulty`, `difficulty_model`, `display_title`,
`display_summary`, `practice_modes`, `figure_paths`, `topic_label`,
`source_answer` and everything else; the run exits 0. This is the trap a partial
re-ingest falls into: use `--upsert` to add a few rows, lose a chapter's
`exam_year` and difficulty ratings, and nothing says so.

The correct pattern already exists in the tree and needs no invention —
`repo:workbench/data/difficulty.py:48-50` writes a targeted `UPDATE` and touches
only the columns it means to.

### P0-3 · a dropped row is reported as success — `DOCTRINE`

```
repo:pipeline/scripts/insert-knowledge-points.py:239-246
    if errors:
        ...
        if args.strict:
            ... return 3
        print(f"\n{len(errors)} validation errors. Continuing with valid rows only...")
repo:pipeline/scripts/insert-knowledge-points.py:297
        return 0
```

Without `--strict` every invalid row is dropped, a note goes to stderr, and the
process still exits 0. Any caller checking `$?` sees success. The `c04` course
worked around it by passing `--strict` at every call site
(`c04:intermediate/c04/problem_extraction/_fixtool/`), which is the only reason
its loss was bounded.

### P0-4 · nothing gates a problem manifest's `kp_ids` against the knowledge points that exist — `NEW-GAP`

The `ncmc` job produced cross-chapter bindings in a side manifest
(`kp-links.chNN.json`, 81 problems / 104 edges) and tagged problems from
`problem-insert.chNN.json`, which carries only `kp_ids`. The loader reads
`kp_ids`. The cross-chapter judgement was therefore dropped, orphan counts were
inflated, and the defect recurred on the next run
(`ncmc:_work/kb/orphan-kp-review.md:230,240,242,265`).

The same gap admits a shell manifest: `pool-insert.ch07.json` and `ch08.json`
were `knowledge_points: []` / `kp_count: 0` and were treated downstream as the
real content of 100 knowledge points
(`ncmc:_work/kb/syllabus-coverage-audit.md:16,116`; `patch.py:7-11`). The tool
would have refused them — `repo:pipeline/scripts/insert-knowledge-points.py:248-250`
returns 3 on an empty manifest — but the hand-written batch driver skipped them
before calling it (`ncmc:_work/kb/tools/dryrun_kp_insert.py:39`).

There is no gate anywhere between per-item field validation and the
post-hoc `validate-pool` sweep, so an entire chapter can be built from a
manifest that references knowledge points nobody ever ingested.

---

## P1 — output cannot be trusted, or cannot be checked

### Ingest integrity

| # | defect | evidence |
|---|---|---|
| 1 | `difficulty check/apply` documents itself as validating a *complete* batch but checks only non-empty plus per-item validity — a truncated batch passes | `repo:workbench/data/difficulty.py:9-14` (`check` docstring "Validate a complete rating manifest"; `:13-14` only rejects empty), `:42-43` |
| 2 | `COLLAPSED_SUBPART_PATTERN` rejects valid Chinese calculus typography. The pattern `[^\n][ \t]+[a-j]\s*\)[ \t]+` matches the `- a) ` inside `(b - a) `, which is ordinary printed maths, not a collapsed subpart list | `repo:pipeline/scripts/candidate_contract.py:12`, used at `:55`; cost: `ncmc:_work/kb/tools/fix_collapsed_subparts.py:7,14-15` records 6 of 180 problems rejected under `--strict` |
| 3 | No manifest schema. The contract is only recoverable by reading the insert script's line numbers; 8 files of one manifest kind carry 9 different key sets | `ncmc:_work/kb/tools/merge_kp_manifests.py:3-4,10` |
| 4 | 8 per-batch builders in `c04`, same contract, three implementations. Only `b07` honours a per-spec `exam_year`; only `b08` emits `display_summary` | `c04:intermediate/c04/problem_extraction/b07/_build/build.py:127` vs `b01:118` / `b02:191` / `b03:122` / `b04:116` / `b05:114` / `b06:125` / `b08:138`; `b08:144-147` |
| 5 | No field distinguishes "the source has no answer" from "extraction failed". Both arrive as `solution: null`, via two different encodings (empty value vs absent key) | `c04:…/b01/_build/build.py:80-81,105-107` — text has a `sys.exit` guard, solution has none; 245/937 rows empty, of which 118 specs keep an empty `s` key and 127 omit it |
| 6 | Knowledge points are extracted per chapter, so all 940 `related_kp_ids` were intra-chapter and 0 cross-chapter; the cross-chapter graph exists only because 218 edges were designed and applied by hand | `c04:intermediate/c04/extraction/_crosslink/crosslink_plan.py:2-5`; 218 cross-chapter / 1149 total edges now in the pool |
| 7 | Shards for ch05/06/08 carried no `kp_id`, so ids were reassembled by position — adding or removing one knowledge point renumbers the rest of the chapter. This has already written wrong shards once | `c04:…/extraction/_crosslink/apply_crosslink.py:105,32-38`; `restore_shards.py:4` |
| 8 | Graph verification reads the manifests and never the database, while the authoritative `knowledge_relations` table stays empty | `c04:…/extraction/_crosslink/verify_crosslink.py:2-4,22-24,51`; `knowledge_relations` = 0 rows, verified |
| 9 | Relation fields are spelled two ways across chapters (`related` vs `related_kp_ids`) and the tool accepts both | `c04:…/extraction/_crosslink/apply_crosslink.py:78-79` |

### Observability — the ledger cannot be used to detect loss

| # | defect | evidence |
|---|---|---|
| 10 | `counts_json.accounting` was byte-identical in all 8 per-batch logs (kp 324 / problems 937 / relations 0) and reported 937 while the pool held 974 rows at apply time. The one field that could have revealed the loss was a constant — and the only requirement that reported accounting match recorded counts sits in the *rollback* scenario and compares two figures from the same record, so it cannot catch this | `c04:intermediate/c04/ingest_log/b01-step2.txt:7-11` ≡ `b08-step2.txt:7-11`; `:16` differs per batch (209 vs 177), so the constant is not a copy-paste of the whole log; `openspec/specs/workbench-content-governance/spec.md:173` |
| 11 | Every batch wrote the same `backup_path`, `pool\c04.db.ingest-backup`, overwritten 16 times; the file no longer exists, so only the last snapshot is recoverable | `c04:…/ingest_log/b01-step2.txt:19` ≡ `b08-step2.txt:19`; the path no longer exists (the course `pool/` holds `c04.db`, `backups/` and `ingest/`) |
| 12 | `ingest_batch_id` is NULL on 100% of rows — 937/937 problems and 324/324 knowledge points — across 16 ledger batches, so no batch can be targeted for rollback or traced to its source | verified against `pool/c04.db` read-only; all 16 ledger rows are `kind='problem-patch'`, none rolled back |
| 13 | The knowledge-point ingest never entered the ledger at all: 16 batches, every one `problem-patch` | `c04:…/ingest_log/b01/recipe.json:4` |
| 14 | A dedup plan declaring 847 unique items produced 937 rows; no gate compares the plan against what landed | `c04:intermediate/c04/dedup-plan.json:511` (`unique_items_to_extract: 847`) vs 937 in the pool |
| 15 | The dedup fingerprint is a normalized 50-character prefix, but `problem_text` averages 49 characters — the key is the whole stem. The collapse to 56 groups only reproduces if normalization strips CJK (ASCII-alnum-only); a CJK-preserving 50-char prefix yields 905 groups. Stripping CJK *is* the bug: every Chinese-stemmed problem keys on its punctuation | `c04:…/dedup-plan.json:4`; pool `min/max/avg(length(problem_text))` = 2/569/49.0, 644/937 rows ≤ 50 chars |
| 16 | Difficulty anchors and per-item rating reasons never reach the manifest, so all 937 ratings are an unweighted mean with no recoverable basis | `c04:…/b01/_build/build.py:125-132,133-145`; pool `difficulty_model` = `cognitive-v1-equal-mean` on 937/937 rows. The declared anchor set is also internally inconsistent: a note says 14, `count=len(anchors)` is 15 (`build.py:165-167`) |
| 17 | The `c04` "before" baseline in the repair report is reconstructed by subtracting the expected change from the "after" counts, and the TOTAL delta is a hardcoded literal `0` — the report cannot falsify itself | `c04:…/_fixtool/final_report.py:60-65,72` |

### Render

| # | defect | evidence |
|---|---|---|
| 18 | Server-side rendering escapes the whole text and then escapes the math expression again, so `&` reaches KaTeX as `&amp;` and `<` as `&amp;lt;`. The client-side path escapes once and emits the already-escaped slice, so the same row renders correctly in one surface and breaks in the other | `repo:workbench/server/pages.py:796` then `:816-820`; contrast `repo:workbench/server/static/workbench.js:311` and `:340-345` |
| 19 | Graph search corpus omits `learning_action`, so text written into that field is unsearchable — 8 terms stopped resolving in the `ncmc` graph | `repo:pool/scripts/render-graph-html.py:1313` |
| 20 | The `fragile` status filter is `Boolean(node.fragile)`; in a pool where every knowledge point has non-empty `fragile` the filter selects everything and means nothing | `repo:pool/scripts/render-graph-html.py:1315` |
| 21 | `graph_label` has no uniqueness or semantic constraint and there is no chapters table, so a chapter name placed in `graph_label` renders a whole chapter under one identical label | `repo:pool/scripts/render-graph-html.py:150` (`graph_label or fallback_graph_label(...)`) |
| 22 | The only label check is a character count (`if len(graph_label) > 24`), so any label already truncated to exactly the limit passes. 9 labels in the `ncmc` pool end mid-word, all at exactly 24 — but the cut itself was made by a course-local merge tool, not by this repository, so the repo-side defect is the weak gate, not the truncation | `repo:pipeline/scripts/insert-knowledge-points.py:127-128`; `ncmc:_work/kb/graph-audit.md:118-125,132` |
| 23 | No built-in formula validator. The maths regex is a private symbol in the renderer, so a course that wanted to check its formula spans had to copy the pattern and build its own KaTeX runner, and that pass still left failures. (The span and failure counts the course recorded — 2501 spans, 15 failing — come from its own report and are not re-measured here; the `ncmc` pool holds 6,009 spans in `knowledge_points.body` and 642 in `problem_text`.) | `repo:workbench/server/pages.py` `_MATH_RE` is module-private (`:657`, used at `:802`); `ncmc:_work/kb/tools/audit/_tmp/rich_probe.py:22-27`, `latex2/report.partial.md:1-3` |
| 24 | Textbooks are imported without unescaping HTML entities or normalising heading levels, so `&gt;`/`&amp;` reach LaTeX and `##` headings are lost; the same content then exists in two files and section references stop reproducing | `ncmc:_work/kb/textbook-ocr-audit-01-05.md:47-49,97-101` |

### Schema and contract

| # | defect | evidence |
|---|---|---|
| 25 | `source_location` uses a `§syllabus-chapter.textbook-section` encoding that exists only as human convention, with no schema and no validator. It already produced a wrong section reference and a reference to a section that does not exist | `ncmc:_work/kb/textbook-ocr-audit-01-05.md:114,132,135-139`; `kp-content-audit-12-16.md:38` |
| 26 | `related_kp_ids` and `fragile` have no documented contract, so a course guessed the field types and then had to re-derive them from the insert script | `repo:pipeline/scripts/insert-knowledge-points.py:154-159` requires `fragile` to be a string or null and rejects a bool; the renderer at `render-graph-html.py:1315` treats it as a boolean flag |
| 27 | No shipped validator measures CJK length. A course wrote one using total `len()`, so all 100 knowledge points passed an 800–2500 汉字 bound while their actual CJK counts had a median of 353 — the gate measured the wrong unit and reported success | `ncmc:_work/kb/tools/validate_shards.py`, `measure_body_length.py` (both workspace-local, absent from the repo) |
| 28 | Difficulty anchors are calibrated against items that are themselves inside the rated set, so "zero anchor violations" restates the anchors rather than testing them. A rated item that crossed the ceiling it was supposed to define was ingested anyway | `ncmc:_work/kb/difficulty-crosscheck.md:14,78-82,88,271` |

---

## P2 — cost and friction

| # | defect | evidence |
|---|---|---|
| 29 | No problem read/search/count/validate CLI. 11 of 22 `c04` repair scripts exist to dump, count, index or screen rows; one re-parses the whole manifest inside a loop | `c04:…/problem_extraction/_fixtool/show.py:3,28` and 10 siblings |
| 30 | No dry-run, no multi-chapter orchestration, no database isolation — a dry run required copying the pool and `lessonkit.json` into `%TEMP%` | `ncmc:_work/kb/tools/dryrun_e2e.py:3,42-48`; `dryrun_kp_insert.py:19-23` |
| 31 | No partial→final two-phase commit. A hand-written `shutil.copy2` promotion leaves the partial behind, refuses to overwrite an existing final, and 19 `*.partial.*` files are still on disk | `ncmc:_work/kb/tools/promote_partials.py:5,25-27,37` |
| 32 | A powerShell stdout redirect landed as a literal 0-byte file named `$null` in the course root, and the output it should have captured was never read | `ncmc:$null` (0 bytes, created 2026-10-01 00:39) |
| 33 | Manual fingerprint repair passes produced a "before" figure and a "0 delta" that no independent baseline supports | `c04:…/_fixtool/inspect4.py:3,10` exists only because `final_report.py` could not be trusted (see P1-17) |
| 34 | `recipe.json` files hold *results* (`applied`, `ok`, `batch_id`, `backup_path`), duplicating the `-step2.txt` stdout, and all 24 log files share a 3-second mtime window that contradicts the ledger's `applied_at` — so file timestamps cannot order the run | `c04:…/ingest_log/b01/recipe.json:10-17` vs `b01-step2.txt:12-19`; ledger `applied_at` spans 16:16→22:57 |
| 35 | Repeated re-extraction leaves half-finished state in place: `textbook/probe` (14,371 B) and `textbook/probe2` (4,682 B), with nothing marking which attempt succeeded | `c04:intermediate/c04/textbook/probe*/` |
| 36 | No frozen knowledge-point vocabulary. The consistency rule lives in a hand-written `kp-baseline.json` and is enforced by nobody | `c04:intermediate/c04/kp-baseline.json:4-5` |

---

## Independently recomputed

Re-run read-only by the recorder, not taken from a sweep:

| claim | result |
|---|---|
| `c04` pool size and kind | 937 problems, all `source_kind='final'` |
| `c04` knowledge points / relations | 324 / **0** |
| `c04` `ingest_batch_id` null | 937/937 problems, 324/324 knowledge points |
| `c04` ledger | 16 batches, all `kind='problem-patch'`, 8 applied 16:16–16:17 and 8 at 22:57, `rolled_back_at` NULL throughout |
| `c04` id drift vs the 974-row snapshot | 37 deleted, 0 added, 937 common; of those **425 hold a different question**, 512 unchanged (P0-1) |
| `c04` problem-id contiguity | live pool and the 974-row snapshot are *both* contiguous 1..N in all 8 chapters — so contiguity is uninformative and is not used as evidence |
| `c04` `exam_year` empty | 372/937 |
| `c04` `solution` empty | 245/937 |
| `c04` `display_summary` set | 3/937 |
| `c04` `problem_type` mix | explanation 481 + other 285 = 766/937 (81.7%) |
| `insert-problems.py` upsert column list | 6 columns (`repo:pipeline/scripts/insert-problems.py:256-259`) |
| `insert-knowledge-points.py` upsert column list | 11 columns (`repo:pipeline/scripts/insert-knowledge-points.py:254-259`) |
| non-strict drop path | prints and falls through to `return 0` (`repo:pipeline/scripts/insert-knowledge-points.py:239-246,297`) |
| collapsed-subpart pattern | `[^\n][ \t]+[a-j]\s*\)[ \t]+`, used at `repo:pipeline/scripts/candidate_contract.py:55`; matches `- a) ` inside `(b - a) ` |
| `difficulty` check coverage | non-empty + per-item only (`repo:workbench/data/difficulty.py:13-14`) |
| double escape | `repo:workbench/server/pages.py:796,816-820` vs `repo:workbench/server/static/workbench.js:311,340-345` |
| graph search corpus / fragile filter | `repo:pool/scripts/render-graph-html.py:1313,1315` |
| graph label fallback | `repo:pool/scripts/render-graph-html.py:150` |
| `fragile` contract | string or null, bool rejected (`repo:pipeline/scripts/insert-knowledge-points.py:154-157`) |

**Verified after the first draft, by diffing the 974-row snapshot:** 37 ids
deleted, 0 added, and 425 of the 937 surviving ids now hold a different question
(P0-1). An earlier version of this file claimed no per-row snapshot existed and
listed the 974 → 937 difference as unverified; both were wrong —
`c04:pool/backups/c04-before-spacingfix-20261001-003817.db` settles it directly.

**Unverified, and therefore not claimed:** which of the 143 prefix-dedup skips
were true duplicates; the correctness of the 419 hand-written problem → KP
assignments; the classification accuracy of the 284 rows whose `display_title`
carries a `【…】` prefix (935 is the count of non-empty titles overall, not of
prefixed ones); the `ncmc` pool counts (5 over-long bodies, 9 truncated labels, 66
of 100 knowledge points, 180 problems, 81/104 cross-chapter bindings, 2501 formula
spans, 15 failing) — these come from sweeps that read the pool but were not re-run
here.

---

## Refuted hypothesis

The `c04` sweep was asked to confirm that knowledge points for ch05–ch08 were
ingested *after* problem extraction had already tagged problems, leaving those
chapters' knowledge points referenced by zero problems. **That is not what the
pool shows.** Per-chapter reference counts, all non-zero:

```
ch01 578/382   ch02 672/348   ch03 434/235   ch04 324/177
ch05 225/150   ch06 128/83    ch07 237/155   ch08 172/108
```

These are **total problem → knowledge-point references, grouped by the knowledge
point's own chapter, over distinct problems** — not a count of distinct knowledge
points. A chapter owns only 32–50 knowledge points, so the first column cannot be
read as "referenced KPs". Zero dangling references, zero empty `kp_ids`.
`kp-baseline.json` is timestamped between the two pre-ingest pool
snapshots, so the vocabulary was frozen before problems arrived. The orphan
population is 22 of 324, not 169.

The lesson is recorded because the gap that let the hypothesis form is real
even though the incident is not: there is no gate that would have caught it
either way (P0-4). The event that *did* happen is different and is P0-1.

---

## Reproduction

All read-only. Run from the pool directory of the named course.

```powershell
# P0-1 — id drift: diff the live pool against the 974-row pre-deletion snapshot
cd 'D:\Documents\Document_In_University\课程\2026-2027 秋冬 大二上\宏观经济学（甲）\pool'
#   snapshot: backups\c04-before-spacingfix-20261001-003817.db   (974 rows)
#   compare problem_id sets, then normalized problem_text on the common ids
#   expect: 37 deleted, 0 added, 425 of 937 common ids holding a different question
#   do NOT use the _fixtool\_backup shard copies — they are post-deletion and give 0

# P0-1, P1-12 — ledger and per-batch provenance
python -c "import sqlite3;c=sqlite3.connect('file:c04.db?mode=ro',uri=True);q=lambda s:c.execute(s).fetchall();print(q('select count(*) from knowledge_relations'));print(q('select count(*) from problems where ingest_batch_id is null'));print(q('select count(*) from knowledge_points where ingest_batch_id is null'));print(q('select batch_id,kind,applied_at,rolled_back_at from ingest_batches order by batch_id'))"

# P0-2, P0-3, P1-1, P1-2, P1-18..21 — read the cited lines in this repository
#   pipeline/scripts/insert-problems.py:256-259
#   pipeline/scripts/insert-knowledge-points.py:239-246,254-259,297
#   pipeline/scripts/candidate_contract.py:12,55
#   workbench/data/difficulty.py:9-14,42-43,48-50
#   workbench/server/pages.py:796,816-820
#   workbench/server/static/workbench.js:311,340-345
#   pool/scripts/render-graph-html.py:150,1313,1315
#   pipeline/scripts/insert-knowledge-points.py:127-128   (the 24-char graph_label gate)
```
