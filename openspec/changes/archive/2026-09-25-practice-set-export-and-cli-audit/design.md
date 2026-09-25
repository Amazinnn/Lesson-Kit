# Design — Practical set export and a checkable CLI surface

## What exists and what is missing

`pull.select` (Domain) already reads formal problems by knowledge point, filters
by `source_kind`, `origin_kind`, the derived `source_group`, and the objective
difficulty vector, orders by weakness, random, or source order, and reports a
per-knowledge-point `shortage`. The HTTP `/pull` handler returns its whole rows;
the CLI projects them down to identifiers, drops `include_ids` (which has its own
spec requirement), and offers no way to turn a selection into an artifact. The
two printable files the problem-set view describes (`-problem-set.md`,
`-solutions.md`) are produced by hand from a template, and the standing guard
only checks that files exist.

Meanwhile the declared interface map drifted from the code. That is the deeper
defect: capability ownership was written down in prose and never checked, so
"which surface owns this?" has no answer that stays true.

## Naming

There is no new user-facing noun. A practice set *is* a practice: the learner's
problem set is the same object the practice page pulls, only pinned to a
manifest and printed. The CLI verb stays `pull`. `plan` is an input manifest in
the same sense as the difficulty and attempt manifests, not a new entity, and
nothing about a practice set is stored durably in this change.

## Composition: one command, six ways in

```
lesson-kit pull <workspace> [selection] [--n N] [--plan <file>] [--print <dir>]
lesson-kit pull <workspace> check --input <file|->
```

Selection is a fixed pipeline so the result is explainable and reproducible:

1. **Candidate set** — knowledge-point scope (explicit `--kp`, else the active
   chapter lens), single-problem ids (`--problem`, repeatable), or every formal
   problem when both are absent.
2. **Conditional filters** — `--source-kind`, `--origin-kind`, `--source-group`,
   `--exam-year` (prefix match), and the objective difficulty range. Filters
   apply to the candidate set only.
3. **Learner drivers** — `--weak` (rank knowledge points by
   `weak.score_all` and take their problems), `--due` (problem rows from
   `queries.due_list`), `--wrong` (`problem_progress` in `wrong`/`stuck`, or the
   latest attempt recorded as wrong). Drivers are a union, not an intersection.
4. **Explicit additions** — `--problem` ids are appended even when they fail
   steps 1–3, so "add this one too" always works.
5. **Order and cap** — source order by default, weakness order under `--weak`;
   `--n` caps the set and unfilled knowledge points stay in `shortage`.

Every selected problem carries a `reason` (`scope`, `weak`, `due`, `wrong`,
`explicit`) so the manifest explains itself and a human can audit the set.

**Fact worth recording:** the existing `mode="weak"` orders by *how many of the
requested knowledge points a problem covers* — it is not the weakness score.
The learner-driven `--weak` in this change uses `weak.score_all`, which is the
real weakness ranking used by the rehearsal suggestions. Both keep their
current behaviour; the difference is documented rather than merged.

## The manifest

A practice manifest is UTF-8 JSON: a title, an optional note, and the ordered
problem ids with their reasons. It is validated before use (every problem
exists, no duplicates), and re-running the same manifest reproduces the same
set — it is an input, not a record. No practice-set row, table, or index is
added to the pool.

## Rendering

Rendering is a pure text rule, so it lives in Domain (`domain/practice_set.py`)
with file IO left to the caller:

- continuous numbering shared by both files;
- the student file contains the problem text and nothing else — no answer, no
  solution, no `problem_id`, `kp_id`, or `source_kind`;
- a missing `solution` renders as `待补` in the solution file, never as an empty
  entry, and the solution file mirrors the numbering exactly;
- figures referenced by a problem stay as their stored relative references, so
  the printed file is stable and the bytes are not duplicated;
- optional title, otherwise derived from the scope.

Defaults put the two files where the existing problem-set contract expects them
(`output/{course}/{chapter}/{chapter}-problem-set.md` and `-solutions.md`), so a
single-chapter set keeps the documented paths; a set spanning chapters passes
`--print <dir> --name <base>`.

## Relationship to the standing guard

`guard problem-set` keeps governing the hand-driven view workflow: its five
intermediate artifacts and the two checks. The CLI-produced set does **not**
fabricate those intermediates, and the guard is not widened to accept it — two
paths pretending to be one gate is how the drift started. Instead the export
carries its own `check`: a zero-write validation of the manifest and of the
rendered files (answer leakage, numbering alignment, duplicate problems,
unfilled knowledge points). The registration documents state which path a reader
is on.

## Machine-checked surface

One ownership table declares every API route and every CLI command with its
audience (Agent, human, both, browser-only) and status. A test derives the real
sets from the argument parser and the route table and fails when:

- a declared command or route does not exist,
- a real command or route is undeclared,
- an entry is declared reachable from both surfaces but one side is missing.

The human registration document (`docs/action-graph/L2-interfaces.md`) keeps its
readable tables and points at the machine authority; its counts are corrected.
This is the mechanism that keeps the answer to "which surface owns this?" true
after every later change.

## Compatibility, data safety, and non-goals

- `exam_year` is additive and nullable: `ensure_columns` only, no default, no
  backfill, no rewrite. Legacy rows stay valid; an unmigrated pool answers with
  the exact `migrate-progress.py` command only when the year filter is actually
  used.
- The CLI keeps its old `pull` shape behind `--ids`; the API response shapes and
  the practice page are unchanged; `weak`, `due`, and `ls` keep their text
  default and gain `--json`.
- The four audited gaps are fixed to match their API counterparts, not beyond:
  `practice` becomes transactional with an existence check, `feedback` gains the
  card type and direction, `goals` invalidates the cached plan like the API
  already does.
- Non-goals: durable storage of a practice set, practising *from* a stored set,
  a papers table or original-paper reproduction, any UI change, and any write to
  a real learning pool during development.
