# File Contract

Intermediate files are explicit agent-facing artifacts. Do not replace them
with private reasoning, final prose, or a claim that a step was considered.

## KP Extraction

Path:

```text
intermediate/{course}/extraction/{chapter}/
```

Required files:

```text
01_inputs/source-scope.md
02_analysis/knowledge-points.md
02_analysis/knowledge-relationship-analysis.md
02_analysis/kp-consolidation-analysis.md
02_analysis/coverage-check.md
02_analysis/pool-insert-manifest.json
04_checks/pool-validation-report.md
```

## Problem Extraction

Path:

```text
intermediate/{course}/problem_extraction/{chapter}/
```

Required files:

```text
01_inputs/kp-query-result.json
01_inputs/full-problem-bank.md
02_analysis/problem-insert-manifest.json
04_checks/problem-pool-validation-report.md
```

## Agent Content Ingest

Agent-created knowledge points, problems, flash cards, and their figures use
one complete JSON manifest:

```text
content-bundle
```

A bundle may contain `knowledge_points`, `problems`, `flash_cards`, and each
problem's `figures`. Items reference each other by a bundle-local `key`; ids are
allocated by the server in course/chapter order. Large manifests are staged under
the owning conversation's `.lessonkit/jobs/conv-NNN/` directory and referenced
from the action by file name (the server refuses absolute paths and `..`); a small
manifest may also be inline in the reply, naming itself with `kind` or `type` as
`content-bundle`. Every knowledge point, problem, and card resolves exactly one
chapter — its own `chapter`, else the bundle-level one — and an item that
resolves none is refused with its label: the workspace's active chapter is never
a fallback, so a multi-chapter manifest cannot be silently assigned to the
chapter the learner happens to be viewing.

The manifest is checked and applied through the workbench ingest boundary as one
prevalidation, one recoverable backup, and one transaction, recording one batch
per chapter present (`batch-NNN` each, in chapter order) so a chapter can be
rolled back on its own. Any invalid item or missing required image leaves SQLite
and the figure destination untouched. Source figures are copied byte for byte into
`.lessonkit/figures/{course}/{chapter}/` and referenced by logical path.

An objective item declares its practice form with `quiz_type` (`yes_no`,
`single_choice`, `multiple_choice`) plus `options`, and optionally an
`answer_key` together with `error_reason`. A **missing answer key is allowed**:
the item is then practised in its 判断/小测 shell without a verdict, and the key
can be supplied later with `lesson-kit data <workspace> update problem <id>
--input '{"answer_key": "…"}'` (an empty value clears it again). The stem bound
is 800 characters.

Problems that already exist are changed **in place** — never by deleting and
re-importing, because the readable id is the row's identity and everything a
learner has recorded hangs off it:

- one row: `lesson-kit data <workspace> update problem <id> --input <file>`;
- many rows: a `problem-patch` manifest (`{"kind": "problem-patch", "items":
  [{"problem_id": "…", …fields}]}`) applied with `lesson-kit ingest <workspace>
  recipe problem-patch --input <manifest> --output <dir> --apply`, which
  prevalidates every item, refuses unknown ids and unknown field names, writes
  one recoverable backup and one transaction, records one batch id together with
  **each row's previous values**, and can therefore be undone value-for-value
  with `ingest rollback --batch batch-NNN`.

Writable fields are the problem's descriptive ones plus its practice form:
`problem_text`, `solution`, `kp_ids`, `problem_type`, `source_kind`,
`origin_kind`, `source_evidence`, `source_answer`, `solution_origin`,
`topic_label`, `display_title`, `display_summary`, `exam_year`,
`practice_modes`, `micro_quiz`, and the `answer_key` shorthand. A patch cannot
change a `problem_id`, and difficulty stays with `lesson-kit difficulty`.
Changing `kp_ids`, `problem_text`, `solution`, or `problem_type` clears the
difficulty rating group as before.

Every problem carries both provenance axes: `source_kind` describes the
grounding material and `origin_kind` describes whether the problem is sourced,
adapted, or generated from it, plus non-empty `source_evidence`. A
source-provided short answer lives in `source_answer`, separate from the
detailed `solution`, whose origin is labelled by `solution_origin`
(`source` vs `generated`). Difficulty fields never belong to an ingest manifest;
explicit rating uses the separate `lesson-kit difficulty` transaction.

Legacy `flash-card-patch` and `micro-quiz-patch` manifests remain accepted.

Successful applies store a manifest snapshot under the pool's ingest area and
stamp a readable batch id. Failed gates write no content. There is no candidate
artifact, candidate table, promotion step, or staging state.

## Course Learning Network

Low-level audited relations may be added after KP extraction.

Optional relation manifest:

```text
intermediate/{course}/extraction/{chapter}/02_analysis/relation-insert-manifest.json
```

Legacy optional learner signal map:

```text
intermediate/{course}/signals/{chapter}/signal-map.json
```

These files do not replace the required KP extraction files. Relation manifests
store durable point-to-point graph facts. New learner signals are stored in the
course SQLite pool. Signal-map JSON stays available only as a compatibility or
handoff input for Focus Map queries.

## Problem-Set View

Path:

```text
intermediate/{course}-{chapter}/problem-set/
```

Required files:

```text
01_inputs/view-scope.md
02_analysis/problem-query-result.json
03_plans/selection-plan.md
04_checks/problem-set-check.md
04_checks/solution-sync-check.md
```

Outputs:

```text
output/{course}/{chapter}/{chapter}-problem-set.md
output/{course}/{chapter}/{chapter}-solutions.md
```

## Workbench Runtime Areas

Runtime assets follow the hidden dot-directory convention and live under
`.lessonkit/`:

```text
.lessonkit/
├── state.yaml                                   # runtime state (tracked)
├── figures/{course}/{chapter}/{owner_id}-fig-{NNN}.png   # tracked
└── jobs/conv-NNN/                               # provider state/events/mirror (gitignored)
```

### Figure Area

- Path: `.lessonkit/figures/{course}/{chapter}/`
- Naming: `{owner_id}-fig-{NNN}.png`, owner is a knowledge point or problem id.
- The pool stores only logical paths on `knowledge_points.figure_paths` and
  `problems.figure_paths`; each display surface resolves them (workbench static
  service; exported Markdown computes document-relative paths).
- Problem figures exist because diagrams are often part of the question itself
  (Karnaugh maps, circuit/force diagrams).
- The extraction pipeline MUST land figures (knowledge-point figures and
  problem-embedded figures) during extraction; views never invent figures.

### Conversation Area

- Path: `.lessonkit/jobs/conv-NNN/`
- Provider-native storage remains the full conversation authority. Lesson Kit
  stores provider session pointers, turn events, and successful mirrored
  exchanges for navigation and display.
- Failed/cancelled output, hidden reasoning, raw protocol events, and ordinary
  navigation are not durable transcript content.
- The whole jobs area is excluded from version control.

## Rules

- Inputs preserve source facts and user intent.
- Analysis files preserve extracted data and mappings.
- Plans decide selection, ordering, and rendering.
- Checks state pass/fail, broken rule, return layer, and repair action.
- Student-facing problem sets must not show internal IDs, KP mappings, or
  solution text.

## Runtime Guard

`lessonkit.py guard` is the v1 phase guard for this contract. It checks that
the required files for a command exist and that check files do not contain
blocking markers such as `Result: FAIL`, `Status: FAIL`, table-cell `FAIL`, or
non-zero `ERROR` counts.

By default, guard only depends on tracked intermediate artifacts and rendered
outputs. For `extract-chapter` and `extract-problems`, passing
`--db pool/<course>.db` also runs `pipeline/scripts/validate-pool.py` and
blocks on its non-zero exit codes. This keeps source-only review lightweight
while allowing stronger local validation when the ignored SQLite pool exists.

Guard coverage:

```text
extract-chapter   -> KP Extraction
extract-problems  -> Problem Extraction
problem-set       -> Problem-Set View plus rendered outputs
```

With `--apply`, the guard writes `.lessonkit/state.yaml`:

- PASS sets `phase: complete`, clears `blocked_reason`, and records
  `next_action`.
- FAIL sets `phase: blocked`, records the first missing artifact or blocking
  marker, failed pool validation, or missing DB, and exits with code 2.

Runtime state is a recovery checkpoint for agents. It is not a substitute for
the intermediate files or for the SQLite pool.
