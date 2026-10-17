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
--input '{"answer_key": "…"}'` (an empty value clears it again). Objective
stems have no length limit.

Before a new problem is written, its normalized whole-stem identity is compared
with every existing problem in the course and with the other items in the same
manifest, across chapters. Case, whitespace, punctuation, known math-rendering
variants, and export-noise lines are normalized; the comparison is not
truncated. A duplicate is refused with the colliding problem id and source
evidence. Similar but different stems remain valid.

The read-only hygiene report is `lesson-kit data <workspace> audit`; select
checks with repeated `--check` options and use `--json` for machine output. It
reports duplicates, likely fragments, unmarked objective items, missing display
titles, unresolved figure references, and orphaned figure files. It exits 0
when selected checks are clean and 1 when they report findings.

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
`display_title`, `display_summary`, `exam_year`,
`practice_modes`, `micro_quiz`, and the `answer_key` shorthand. A patch cannot
change a `problem_id`, and difficulty stays with `lesson-kit difficulty`.
Changing `kp_ids`, `problem_text`, `solution`, or `problem_type` clears the
difficulty rating group as before.

`topic_label` is not a problem field and problem manifests reject it. It remains
an optional field on flash cards only.

Every problem carries both provenance axes: `source_kind` describes the
grounding material and `origin_kind` describes whether the problem is sourced,
adapted, or generated from it, plus non-empty `source_evidence`. A
source-provided short answer lives in `source_answer`, separate from the
detailed `solution`, whose origin is labelled by `solution_origin`
(`source` vs `generated`). Difficulty fields never belong to an ingest manifest;
explicit rating uses the separate `lesson-kit difficulty` transaction.

Legacy `flash-card-patch` and `micro-quiz-patch` manifests remain accepted.

Valid content-bundle checks and successful content-bundle applies add a
`typesetting` report, preserved by `apply_batch`, CLI JSON and Bridge
`action.result`. The pool validator adds the same key to its existing JSON
report and uses the shared text rendering in the existing textual report
(`04_checks/pool-validation-report.md` may capture it as before). It is advisory
and does not change any existing gate result, accounting, or exit code.

```json
{
  "available": true,
  "band": {"min": 40, "max": 300},
  "over_long": [
    {"kp_id": "dmath-ch06-kp-001", "over_long_paragraphs": 1,
     "short_paragraphs": 1, "min_visible_characters": 12,
     "max_visible_characters": 301}
  ],
  "short": [],
  "summary": {
    "knowledge_points": 1, "paragraphs": 2,
    "visible_characters": {"p50": 12, "p75": 301, "p90": 301, "p99": 301},
    "over_long": {"knowledge_points": 1, "share": 1.0},
    "short": {"knowledge_points": 1, "share": 1.0}
  }
}
```

`kp_id` is the provided id, or the local bundle key before allocation. Each
flagged knowledge point appears once: over-long first, then short-only. Shares
are fractions of all checked knowledge points; percentiles use nearest rank
over all measured paragraphs, including zero-visible paragraphs. Empty scopes
have zero counts/shares and null percentiles. `available: false` explicitly
means no input to check (absent bundle, or unreadable pool table/body/id), whereas
`available: true` with empty sections means checked and clean. The pure helper
`ingest.inspect_content_bundle_typesetting(manifest)` exposes that distinction
without adding a CLI command or replacing existing bundle validation.

Successful applies store a manifest snapshot under the pool's ingest area and
stamp a readable batch id. Failed gates write no content. There is no candidate
artifact, candidate table, promotion step, or staging state.

A reviewed Git checkout may additionally supply a `content-bundle` from
`authored-bundles/<course-id>/<chapter>/<name>.json`. This is an input artifact,
not a canonical entity projection. On this path new items MUST use bundle-local
`key` values and MUST omit `kp_id`, `problem_id`, and `card_id`. Check it with
`lesson-kit ingest <workspace> bundle --input <file>`; add `--apply` to enter the
same governed `apply_batch(..., source="cli")` transaction described above.
The read-only form writes no rows, batches, figures, or backup. Apply revalidates
the whole manifest and only the pool allocates canonical ids. The full
repository-side rules live in `docs/github-authored-bundles.md`.

## Git Authored-Content Repository

`lesson-kit mirror` reads and writes a local checkout containing versioned JSON
for the authored-content projection and a separate binary figure projection.
The same checkout may also carry reviewed bundle inputs. The workspace's Course
Identifier selects the course directory; the workspace name and physical path
do not.

```text
<repo>/
├── authored-bundles/<course-id>/<chapter>/<name>.json
├── courses/<course-id>/
│   ├── knowledge/<entity-id>.json
│   ├── problems/<entity-id>.json
│   └── relations/<entity-id>.json
├── figures/<course-id>/
│   ├── _index.json
│   └── <chapter>/...
└── delete-requests/<request-id>.json
```

`authored-bundles/` is a review/versioning input surface. `courses/` is the
canonical authored-content projection of rows that already exist in the pool.
An authored-bundle file therefore never creates a repository-only canonical id;
a successful governed apply creates pool rows first, after which `mirror push`
may export those entities under `courses/`.

Nested folders under `knowledge/`, `problems/`, or `relations/` are allowed.
Files are located recursively, and their embedded `entity_id` is the identity;
renaming or moving a valid file within its entity directory does not create or
delete an entity. Two files with the same entity type and id are invalid.

### Binary figure projection

Each binary file is stored at `figures/<logical-path>`, where the pool logical
path starts with the selected course id (for example,
`dmath/ch06/<sha256>.png` becomes `figures/dmath/ch06/<sha256>.png`). Image bytes
remain outside SQLite and JSON entity envelopes. Only paths referenced by
`knowledge_points.figure_paths` or `problems.figure_paths` participate.

`figures/<course-id>/_index.json` is UTF-8 JSON derived from those pool
references. Push writes it even when no figure is referenced. Its exact envelope
is:

```json
{
  "schema_version": 1,
  "course_id": "dmath",
  "figures": [
    {
      "logical_path": "dmath/ch06/<sha256>.png",
      "owners": [
        {"owner_type": "problem", "owner_id": "dmath-ch06-prob-001"}
      ]
    }
  ]
}
```

`owner_type` is `kp` or `problem`. The index is navigation metadata, not a
membership authority; changing it never changes pool rows or their `figure_paths`.
`check` reports a missing, matching, different, or invalid index without
rewriting it.

`mirror <workspace> figures --repo <checkout> --direction check|push|pull`
requires an explicit direction. `check` and `--dry-run` write nothing. After
legacy identity checks pass, push prefers the workspace's top-level
`figures/<logical-path>` and falls back to
`.lessonkit/figures/<logical-path>`; pull writes both to preserve the current
renderer and ingest layout. Each replacement is atomic for its individual file;
the operation does not roll back previously replaced files after a later
operating-system write failure. It never prunes unreferenced files or invokes
Git network operations.

Figure synchronization reads an existing regular pool database with both the
`knowledge_points` (`kp_id`) and `problems` (`problem_id`) tables. A missing/non-file database or missing
owner table/id column is invalid, not an empty figure set; the command never
creates a database. For older pools, an existing owner table without a
`figure_paths` column is accepted as having no references and is not migrated.

All resolved figure roots and targets must stay inside the registered workspace
or the supplied checkout. The derived index path is checked against the checkout
before any figure copy, including pushes with no references. A symlink or
junction that redirects an asset root or target outside its anchor is refused.

An existing logical filename whose stem is 64 lowercase hexadecimal characters
retains its legacy content-hash identity. If any existing workspace/repository
copies differ, the whole planned operation is refused before writing. Pull also
refuses a repository-only legacy hash file when neither workspace copy provides
a local baseline. An existing local copy may seed the repository or a matching
compatibility copy. Other existing non-hash logical paths remain editable
through an explicit direction. The broader figure naming strategy remains unresolved;
this contract adds no hash computation, rename, or migration.

Each entity file is a UTF-8 JSON object with exactly these envelope fields:

```json
{
  "schema_version": 1,
  "entity_type": "problem",
  "entity_id": "c02-ch01-prob-001",
  "revision": 1,
  "content": {}
}
```

`schema_version` is integer `1` (`true` and `1.0` are invalid). `entity_id` is
an immutable id belonging to the selected course. `revision` is a positive
integer; booleans, fractions, zero, and negative values are invalid. Content
fields are limited to the existing governed authored fields:

- `kp`: `knowledge_item`, `graph_label`, `source_location`, `knowledge_type`,
  `related_kp_ids`, `importance`, `learning_action`, `body`, `difficulty`,
  `fragile`, `figure_paths`.
- `problem`: `kp_ids`, `problem_text`, `solution`, `problem_type`, `source_kind`,
  `origin_kind`, `display_title`, `display_summary`, `exam_year`,
  `source_evidence`, `source_answer`, `solution_origin`, `practice_modes`,
  `micro_quiz`, `figure_paths`, `difficulty_knowledge_breadth`,
  `difficulty_reasoning_depth`, `difficulty_transfer_distance`,
  `difficulty_construction_openness`, `difficulty`, `difficulty_model`.
- `relation`: `source_kp_id`, `target_kp_id`, `relation_type`, `direction`,
  `strength`.

JSON arrays and objects stay arrays and objects in the file. `kp_ids` must be an
array; `related_kp_ids`, `practice_modes`, and `figure_paths` may be arrays or
null; `micro_quiz` may be an object or null. A JSON string containing serialized
array/object text is invalid. Unknown fields and changed embedded identity are
refused. Figure entries must be non-empty strings accepted by the existing
course-relative POSIX path rules: `<course-id>/<chapter>/<filename>` with no
empty, `.` or `..` segments and a supported figure extension. These are logical
references only; JSON mirror sync does not create or transfer figure bytes or
choose a repository-wide naming policy.

The four problem difficulty dimensions, derived `difficulty`, and
`difficulty_model` form one all-null or complete group. Repository edits change
the dimensions; the mirror recomputes the derived fields through the existing
difficulty checker, and a derived-only edit is invalid. A content-axis edit
clears stale difficulty only for columns present in the pool. Explicit ratings
requiring an unavailable group are invalid during check; the mirror does not
migrate or invent pool columns. An older schema omits fields it does not expose.
The mirror remains limited to knowledge points, durable problems, and
relations; it excludes flash-card entities and learner/runtime state, and it
cannot create a repository-only id.

These approved fields are an additive projection within `schema_version: 1`.
An older v1 baseline or file may omit them. A local pool projection is exported
at the next revision; another workspace may adopt a complete matching
projection only at exactly its expected next revision. Revision spoofing,
wrong-revision payloads, and divergent edits remain invalid or conflicting.

A deletion request has exactly `schema_version`, `request_id`, `course_id`,
`entity_type`, `entity_id`, and `reason`. It is validated and reported as
pending; it never deletes pool content. Likewise, a missing entity JSON file is
restored from an existing tracked pool row at a new revision.

`mirror init` explicitly establishes pool-first revision-1 state and adopts an
existing matching file by embedded identity. A file that cannot be read as
UTF-8 JSON is reported with its path and reason; an entity whose id such an
unreadable file names is refused a canonical file until it is repaired, while
unrelated entities still bootstrap. `check`, `status`, and
`sync --dry-run` write neither pool content nor entity JSON. `sync` handles one
entity at a time through existing content validation; successful entities may
remain applied when a sibling is invalid or conflicting. Repository edits,
pool edits, and the remembered normalized content use monotonically increasing
integer revisions without hashes. The command only reads/writes the supplied
local checkout; clone, pull, commit, and push remain external Git operations.

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

Math is preserved verbatim: `$…$` and `$$…$$` are written to both Markdown
files exactly as stored, so the exported set must be read with a
math-capable Markdown viewer (or rendered later) — the workbench page renders
it with KaTeX, the raw file does not.

## Agent Saved Papers

`lesson-kit pull --plan` exports a `practice-set` manifest; `pull --print` writes
student and solution Markdown. Those exports are not managed papers. To add a
manifest to the Workbench saved-paper list, run:

```bash
lesson-kit papers <workspace> save --input <manifest>
```

The manifest uses the existing top-level fields `kind`, `title`, optional
`course`, optional object `request`, optional export-only `shortage`, and
`items`. Each item has `problem_id` and optional `reason`. Save validates the
kind and allowed fields, requires a non-empty ordered list of unique IDs that
exist in the selected workspace, checks any supplied course against that
workspace's active course, and requires a non-empty title and an object request
when supplied. It leaves the input manifest and SQLite unchanged. A successful
command returns `practice_set_id`, `title`, `count`, and the workspace-relative
`url`; a job file or printed sheet is not evidence of a managed save.

Managed papers live at `.lessonkit/practice-sets/ps-NNN.json`. The existing
Data writer stores the paper plan and stable ID atomically; the browser list
reads that same store. Saving does not write learning state or course SQLite.

Corrections target identities explicitly; `save` always creates a new Paper,
never an inferred overwrite by title or similar stem. Optional `description`
is container metadata. Use `papers <workspace> list`, `get <ps-id>`,
`preview <ps-id> --input <manifest>`, `update <ps-id> --input <manifest>
--confirmation <preview.json>`, or `delete <ps-id>`. Preview/update accept an
explicit item list and/or metadata. Metadata and effective no-op updates retain
progress. Changing membership/order requires the current preview's confirmation
object: target order, structure generation and exact unfinished states/drafts.
If those change, obtain and confirm a fresh preview. Updates retain the ID and
do not start practice. Question corrections use `data update problem <existing-id>`
or `problem-patch`; changing answering type does not allocate a new question ID.
Deleting a Paper leaves questions and evidence. Empty/unavailable containers
stay inspectable, repairable and deletable, but cannot start/export. Pending
file publication is Data-owned SQLite state, not manifest content (DATA_MODEL).

These names are v1 compatibility surface: the manifest kind `practice-set`,
the save receipt field `practice_set_id`, the `ps-NNN` IDs, the
`.lessonkit/practice-sets/` store, and `/practice-sets/...` routes remain valid
while the product object is a saved Paper. New active execution and history
rows use `source_kind: paper`; no manifest or saved-file shape changes.

A conversation may end with one `paper_artifact` action that references a
managed Paper by its saved `ps-NNN` id. It carries no manifest, writes nothing,
and is only accepted when that id resolves to a record in the selected
workspace; the Bridge then reads the stored title and item count instead of
model-supplied values. The action has no URL field, and the Workbench derives
the workspace's own `/practice-sets` destination.

## Workbench Runtime Areas

Runtime assets follow the hidden dot-directory convention and live under
`.lessonkit/`:

```text
.lessonkit/
├── state.yaml                                   # runtime state (tracked)
├── figures/{course}/{chapter}/{sha256}.{ext}      # tracked
├── practice-sets/ps-NNN.json                    # reusable saved papers
└── jobs/conv-NNN/                               # provider state/events/mirror (gitignored)
```

### Figure Area

- Path: `.lessonkit/figures/{course}/{chapter}/`
- Naming: `{sha256}.{ext}`, the lowercase SHA-256 of the original bytes plus
  their supported source extension; the figure-patch gate derives this name.
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
