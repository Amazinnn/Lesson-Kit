# File Contract

Intermediate files are explicit agent-facing artifacts. Do not replace them
with private reasoning, final prose, or a claim that a step was considered.

## Agent part grading boundary

The `agent-part-grading` change adds a grading operation separate from attempt
transcription and `attempts correct`. A subjective submission authorizes grading
of that exact submission. A conversation explicitly asking for re-extraction or
review authorizes only the corresponding grading mutation; ordinary discussion
does not authorize writing. The existing installed `attempts`, `practice` and
`content` contract topics remain available; the installed `grading` topic provides
the precise new mutation contract (`python -m workbench.bridge.agent_contracts grading`).

Grading operations must identify the workspace, execution, problem, stable part,
Attempt and content version. Every mutation includes a caller-stable operation
identity and expected current revision. A retried identical operation returns
the original result; changed content under that identity is rejected. Invalid,
stale or conflicting requests leave all rows unchanged. Original learner text
is never replaced with an extracted answer.

The payload separates an optional learner Extracted Answer, optional reference
answer/process with `source` or `agent_derived` provenance, final-answer conclusion,
process conclusion and their explanations. Final-answer conclusions allow
`correct`, `wrong`, `needs_confirmation`, `unprovided`; process additionally allows
`partially_correct`. Inapplicable dimensions are omitted. Withdrawals remove only the
current derived conclusion and retain revision history. No grading payload
silently creates a 1–5 self-rating or learning projection.

Use `lesson-kit <command> --help` and installed detailed contracts for the exact
operation names and target shape. A browser's read-only display is not a second
learner input. Learner API reads and status previews must mask undisclosed
outcomes; authorized Agent raw reads are a separate surface.

The exact command family is `lesson-kit grading <workspace> get|history|retry
--attempt-id N` and `apply|withdraw --input FILE`. Mutation JSON contains
`attempt_id,problem_id,part_id,content_revision,expected_revision,operation_id`
and, for apply, `payload`. Execution is resolved from the saved Attempt context,
not accepted as an alternative caller target. Expected revision is zero for a
new grading, otherwise the latest revision (including a withdrawal). An exact
replay returns its saved revision; changed payload needs a new operation identity.
Retry queues the same submission for the persistent server; it is not a second
submission or a synchronous model call.

Browser draft/submit adapters are POST `/api/w/{name}/practice/part-draft` and
`/practice/part-submit`, with `execution_id,position,practice_context` and
`part_id`; omitting `part_id` on submit means all remaining parts of that problem.
Drafts carry `answer/choices/stuck/reference_viewed` and per-part `sequence`;
submits require stable `request_id`. GET/POST `/api/w/{name}/grading` provides
Agent read/history and `apply/withdraw/retry` actions under the local tool writer
boundary. It is not a learner correction form or a new authentication system.

### Authored problem parts (`problems.parts`)

`parts` is governed authored JSON on a problem row: an ordered array whose saved
order is authoritative — practice renders it as stored and never reorders or
splits it. It is accepted on content-bundle problems and on `problem-patch`
(`lesson-kit data <ws> create|update problem --input`); it is never inferred from
practice state.

| field | required | rule |
|---|---|---|
| `id` | yes | lowercase `[a-z][a-z0-9_-]{0,63}`, unique inside the problem |
| `prompt` | yes | non-empty string |
| `type` | yes | `yes_no` / `single_choice` / `multiple_choice` / `calculation` / `proof` / `open_response` |
| `options` | objective parts | distinct strings, ≥2; `yes_no` defaults to 是/否 |
| `answer_key` | optional | scalar naming one option (`yes_no`/`single_choice`) or a list naming options (`multiple_choice`) |
| `reference_answer` | optional | text; forbidden on `proof` |
| `reference_reasoning` | optional | text (the reference process) |
| `short_answer` | optional | boolean; marks a concise final result that may be extracted |

- One problem may mix judgment, choice, calculation and proof parts; a problem
  without `parts` remains one legacy whole problem. A problem with `parts` must
  not also declare `quiz_type` / `micro_quiz` (the bundle refuses the combination).
- Missing final results stay "unprovided" — never synthesized as wrong; proof
  parts carry process conclusions only.
- Later edits follow existing content-revision invalidation rules for affected
  unfinished practice and never rewrite historical submissions.
- Storage requires the additive migration on older pools
  (`python pool/scripts/migrate-progress.py --db pool/<course>.db`); the bundle
  gate refuses `parts` with an actionable error when `problems.parts` is absent.

## Workspace layout and artifact roots

Lesson Kit's bundled teaching resources are installed package files under
`workbench/resources/skills/source-bounded-learning-drill/`: `SKILL.md` and
`TERMINOLOGY.md` travel together and are loaded by Bridge launch arguments.
They are not course artifacts and are not copied into course roots or Pi global
configuration. Existing manifest and database contracts below are unchanged.

New workspaces put their pool at `.lessonkit/pool/<course>.db`; an unmigrated
legacy workspace continues using its registered root `pool/<course>.db`.
Workbench resolves the workspace from its registered path, not by assuming the
database is always two levels below the course root. Pool-adjacent ingest batch
records and backups follow the selected pool directory.

The pipeline-relative `intermediate/...` and default `output/...` paths below
are resolved under `.lessonkit/` for hidden-layout workspaces. Existing legacy
pipeline artifacts retain their old workspace-relative paths until explicit
migration. The Workbench adapter preserves frozen pipeline command contracts;
direct legacy `lessonkit.py` commands keep their original CWD-based behavior.
Workbench guards also consume newly hidden gate-specific artifacts for an
unmigrated pool: a present hidden gate directory is authoritative; otherwise
the existing root gate directory remains supported. Incomplete hidden work must
fail its check instead of silently passing against stale root artifacts.
Agent-created internal work uses `.lessonkit/intermediate/` or the owning
conversation's `.lessonkit/jobs/` even when reading an unmigrated pool. A
user-specified export path is honored; without one, generated internal work must
not create directories in the course root. Source materials stay in place.

`lesson-kit workspace <name> migrate-layout` previews without writes; `--apply`
explicitly moves only root `pool/` and `intermediate/` into `.lessonkit/` and
updates registration. All backups, batch manifests and history are retained;
known legacy path references are resolved at their consumers. Relative Markdown
link targets may be narrowly rebased to preserve the same existing target after
the move; such edits must be enumerated, not applied as a blanket text rewrite.
No schema/content/learning change, history pruning, destination merging, root
symlink aliases, nested-workspace traversal or external-tool relocation occurs.
Legacy image-reference planning can read newly hidden internal images as well
as existing root intermediate images. Conflicting same-name images across the
two areas must be reported instead of silently selecting different content.

The migration command returns UTF-8 JSON with `workspace`, boolean `applied`,
`moves` (`source`/`destination` pairs), `registration` (`before`/`after` pool
paths), and `link_changes`. Each link-change entry names its relocated `path`,
original-byte `backup`, and `targets` (`before`/`after` tokens). A successful
nonempty apply also returns `receipt`, stored at
`.lessonkit/layout-migration/receipt.json`; original changed Markdown bytes are
kept under `.lessonkit/layout-migration/before/<old-workspace-relative-path>`.
An empty repeat has no moves and does not create another receipt or copy.

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
`answer_key`. A **missing answer key is allowed**:
the item is then practised in its 判断/小测 shell without a verdict, and the key
can be supplied later with `lesson-kit data <workspace> update problem <id>
--input '{"answer_key": "…"}'` (an empty value clears it again). Objective
stems have no length limit. A stored `micro_quiz` payload MAY still contain a
legacy `error_reason`; it is ignored by validation and rendering and is not part
of the current contract.

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

## Agent Attempt Manifests

`lesson-kit attempts <workspace> check|apply --input <file|->` accepts one UTF-8
JSON manifest. `check` validates and previews with zero writes; `apply` commits
the whole manifest atomically or writes nothing.

```json
{
  "request_id": "conv-001-turn-004-record",
  "paper_id": "ps-001",
  "items": [
    {
      "problem_id": "dmath-ch06-prob-001",
      "answer_text": "transcribed learner answer",
      "note": "grading note",
      "rating": 3
    }
  ]
}
```

- `request_id` is required, non-empty, and at most 200 characters. It is the
  idempotency key: the same request id with the same manifest returns the first
  result; the same id with different content or a different `paper_id` is
  refused with zero writes.
- `paper_id` is optional. Without it, the attempt is a free record. With it, the
  value must name one saved `ps-NNN` Paper and every item's problem must belong
  to that Paper's current ordered items. `apply` then binds the attempts to that
  Paper's execution progress in the same transaction: the active execution when
  the Paper is selected, its parked checkpoint when one exists, or a newly
  created `on_submit` checkpoint when it has no unfinished progress. A newly
  created checkpoint is not an active practice and does not create a
  `practice_runs` row. An already answered or stuck item receives a new attempt
  and is re-linked; the earlier attempt remains.
- `items` is required and non-empty. Each item carries only `problem_id`,
  `answer_text`, `note`, and optional integer `rating` 1–5. `answer_text` or
  `note` must be non-empty. One manifest may not repeat a problem.
- `rating` uses the existing learner 1–5 scale. When present, the attempt,
  feedback event, signals, current states, learning progress, and schedule change
  atomically through the existing rules. When absent, only the attempt and any
  Paper execution progress change; learning projections do not.
- The manifest carries no image bytes, image paths, exam marks, or grader
  identity. Answer images stay in the learner's registered directories.
- `correct <attempt-id> --input <file>` replaces one Agent-recorded attempt and
  its linked evaluation with the existing snapshot/withdraw/recompute rules; it
  does not create a new attempt row.

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
An explicit `append <ps-id> --problem <problem-id>` adds one existing problem at
the end without resetting existing item states, attempt links, drafts, or
progress. It increments the Paper's structure generation, updates the matching
active or parked execution, and is idempotent: appending an already present
problem returns `already_present` with zero writes. It is not the membership/order
update path and does not require that path's reset confirmation. Deleting a Paper
leaves questions and evidence. Empty/unavailable containers stay inspectable,
repairable and deletable, but cannot start/export. Pending file publication is
Data-owned SQLite state, not manifest content (DATA_MODEL).

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
├── pool/{course}.db                             # new/explicitly migrated workspace
├── intermediate/                               # internal build/audit artifacts
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
  stores provider session pointers, per-turn artifacts/events, and successful
  mirrored exchanges for navigation and display. Before provider dispatch, a
  turn artifact stores the accepted user text and captured context; when a
  `submission_id` is supplied, it also stores that identity and the stable
  submitted task fields. A pending message keeps its current `message`, the
  immutable `accepted_message`, and `queue_revision`; edits change only the
  current text and revision. Delivery action (`queue` or `interrupt`) is
  routing metadata, not part of task identity. An explicit retry links its new
  turn with `retry_of`, uses the current accepted text, and reuses the original
  captured context.
- `conversation.json` stores `queue_order`, the ordered turn IDs whose current
  status is `queued`. New conversations start with an empty array. A legacy
  conversation with no field reads queued turns in numeric turn-ID order and
  is not rewritten by reads; the first successful queue mutation writes the
  explicit order. Accepted ordinary queue messages append to this order;
  removal, dispatch, and send-now promotion remove the corresponding ID.
  `waiting_for_stop` handoffs never appear in `queue_order`. Session GET
  exposes the confirmed `queue_order`, and each message includes its current
  `queue_revision`.
- Turn artifact status `queued` or `waiting_for_stop` denotes accepted work
  that has not begun provider execution. The interrupt turn records its
  captured `interrupt_target_turn_id` and runs only after that turn is terminal
  and its worker releases ownership. `conversation.json` may include
  `queue_paused`; missing on older conversations means false. Failures,
  unexpected interruption, service recovery, and a completed interrupt turn
  leave retained ordinary work paused until an explicit queue continuation.
  Recovery never converts an unstarted interrupt handoff into queued work or
  replays it automatically.
- `POST .../turns` accepts optional `queue_action` (`queue` by default or
  `interrupt`) and returns the accepted turn fields at the top level. Pending
  edits use `PATCH .../turns/{turn_id}` with `expected_revision`; pending
  removal uses `DELETE` on the same path with `expected_revision` and retains a
  cancelled history entry. Stale or already-running mutations conflict without
  changing the turn.
- Session reads expose pending messages, their revisions, and queue state, but
  not captured context. `POST .../queue/continue` returns
  `{conversation_id, queue_paused, turn}`; `turn` may be null for a handoff.
- `POST .../queue/reorder` accepts
  `{expected_order, turn_ids}`. Both are complete arrays of turn IDs;
  `turn_ids` must be an exact permutation of `expected_order`. Under the same
  conversation ownership lock used by dispatch, the service compares
  `expected_order` with the current confirmed queued order and verifies that
  every member remains eligible. A malformed request returns HTTP 400; a
  stale order or ineligible queued entry returns HTTP 409 with no mutation.
  Success returns `{conversation_id, queue_order}`.
- `POST .../turns/{turn_id}/interrupt` accepts
  `{expected_revision}` to promote one existing queued message into the direct
  interrupt-and-send path. It returns that turn's canonical top-level response
  and preserves its accepted identity, current edited text, submitted fields,
  and captured context. A promoted turn is durably marked in its existing turn
  artifact so repeating the same request returns that turn's current canonical
  state, even if its revision has advanced, without a second cancellation or
  execution. A revision mismatch before first promotion, a started ordinary
  target, an ineligible target, another handoff, or pending Paper approval
  returns HTTP 409 without changing the queued item. If idle,
  the promoted message starts directly even when older queued work is paused;
  those peers retain their order and paused state. If a turn is running, the
  promotion waits for that captured worker's terminal state and release.
- An Agent may propose a membership/order change to one existing saved Paper in
  a `paper_update_proposal` action containing only `practice_set_id` and ordered
  `problem_ids`. The bridge resolves the Paper in the selected workspace and
  stores the proposal and Data preview snapshot in that proposing turn's
  `paper_approval` artifact. This artifact binds `workspace_name`,
  `conversation_id`, `turn_id`, Paper id, and an approval `revision`; its
  `confirmation` is the private `practice_sets.preview_update` snapshot used by
  the existing writer. No Paper update occurs when the proposal is emitted.
- Session GET exposes `pending_paper_approval` (the current public projection,
  or null). The proposing assistant message keeps an `action` envelope with
  `type: paper_update_proposal`, the proposal fields, and its current
  `paper_approval` projection. The projection includes the current and proposed
  ordered question ids, additions/removals, order and reset flags, and
  preview-derived completed-item and draft counts; it does not expose the
  private confirmation snapshot.
- `POST .../paper-approval` accepts
  `{turn_id, expected_revision, decision}` where decision is `approve` or
  `cancel`. It returns
  `{conversation_id, turn_id, approval, queue_paused, stale}`. Approve
  revalidates the stored Data snapshot before delegating to
  `practice_sets.update_saved`; cancel changes only the approval artifact.
  When the Paper/progress snapshot changed, the response has `stale: true`, a
  refreshed pending projection, and a new revision; it performs no Paper write
  and requires another click with that revision. A resolved same-decision
  retry returns the stored result without running the writer again. Invalid or
  unavailable proposals resolve as `invalid` and never recreate a Paper.
- A pending approval pauses its conversation before the proposing turn hands
  off to queued work. It blocks queued and interrupt dispatch and manual queue
  continuation. New messages remain queued. Approval or cancellation leaves
  the backlog paused for explicit manual continuation. Reload/recovery restores
  the pending projection and pause from the existing conversation/turn files;
  no new approval database or event kind is introduced. Other conversations
  are independent. Existing manual Paper CLI and UI workflows remain unchanged.
- Practice draft answer, note, choices, and visible images enter that turn
  snapshot only when the request opts in with `include_draft`; the bridge bounds
  them. They are not Pool learning records, are not copied to the successful
  transcript, and are not inherited by later turns.
- History projects accepted messages and truthful terminal status from turn
  artifacts alongside the successful transcript. Legacy successful exchanges
  remain visible once. Failed/cancelled turns may retain only actual, bounded,
  redacted public partial output; missing messages or output are never invented.
- Hidden reasoning and raw protocol events are not durable transcript content.
  Tool activity summaries, details, and outputs are sanitized and bounded.
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

## Agent resources settings API
浏览器入口：GET/PATCH/POST `/api/w/{name}/agent-resources`；GET/PATCH/DELETE `/api/w/{name}/agent-resources/skills/{skill_id}`。URL 工作区需有效，资源作用域为用户全局。根 PATCH `{instructions: string}`；POST `{source_path: string, replace?: boolean}`；Skill PATCH `{enabled: boolean}`。详情返回 body/entry。非法输入 400，未知 Skill 404。重复 ID 必须显式 replace=true，内置文件不可覆盖/删除。导入拒绝链接及受管目录递归导入，不执行脚本。
每轮 agent_resources 只含启用目录和全局要求，continuity 含最近两轮成功原文；它们不是新授权或执行回执。Metadata 识别 YAML name/description 标量及折叠/字面块，或 Markdown 标题/首段，原文及附属文件保留。无兼容 YAML 的入口走路径读取，不冒充 Pi 原生包。


## Course exchange implementation boundary (WP01 in progress)

The `expand-file-mediated-course-sync` change owns this new boundary. Existing mirror artifacts retain their declared format. The course exchange v1 manifest follows the exchange matrix and is not an implicit upgrade of mirror JSON.

The internal pure comparison `plan_exchange(base, local, incoming)` accepts maps keyed by persistent asset identity. Each value has `kind`, `content`, optional `depends_on` identities and optional explicit `deleted` flag. Absent assets never imply deletion. Comparison uses these semantic fields, excluding transport revisions. Drafts are projected per execution/question position. Historical facts use persistent origin/record identities.

The plan returns deterministic `changes` (incoming to local), `outgoing` (local to incoming), `conflicts`, `errors` and `unchanged` lists. Mutations contain `identity`, `action` (`create`, `update`, `delete`) and the selected `asset`. Conflicts contain complete `base`, `local`, `incoming` projections. Errors contain `identity`, `code`, `message`. Invalid dependency groups remain unchanged while independent valid units continue. The planner does no IO and never mutates inputs. Concrete persisted v1 payload and writer mapping are completed before exposing export/receive as delivered.

The confirmed learning preference file `.lessonkit/course-preferences.json` is a managed course asset. GET/PATCH `/api/w/{name}/course-preferences` reads or saves validated course-scoped learning keys through Data. The preference writer owns its precise JSON envelope, documented with its implementation and regression checks before delivery. Browser-only unconfirmed values are not exported as saved state.

### Course exchange v1 persisted projection (WP01 in progress)

`manifest.json` contains integer `format_version=1`, `course` (`id`, stable `origin`), installation `origin`, readable `export_id`, `assets` descriptors and the established `base` projection. Each descriptor has `identity`, `kind`, relative JSON `path` and `depends_on`. Its JSON envelope contains `kind`, `content`, `depends_on`, and explicit `deleted` when applicable. Row content contains `table`, the ordered primary-key `key`, and every source `row` field. File content contains its workspace-relative `path`, `encoding=base64` and `data`, preserving exact bytes. No incoming SQL is executable. Unknown tables, asset kinds, format versions and unsafe paths are explicit failures. Missing descriptor files produce errors and cannot authorize deletion.

The workspace `.lessonkit/course-sync/state.json` stores course/installation origins, persistent local-row identity mappings and the established shared base. It is synchronization metadata, not a learning fact and is never copied as an ordinary course file. Optional `.lessonkit/course-sync/config.json` registers additional workspace-relative `managed_paths` for source originals and learning files, and its `media` object records the configured exchange medium (`package` directory inside `repo`, `branch`, `remote`) written by `course-sync <workspace> schedule install`. Managed Paper files, goals, confirmed learning preferences, registered learning files and referenced figure bytes are included by their existing owners. Native Provider sessions, credentials, locks and PID files are excluded from this projection. The exporter reports its covered table/file inventory. Full package acceptance additionally requires the receive-side mappings and runtime consumers.

Integer record identifiers in row payloads are exchanged as their stable asset identities, including declared attempt/execution references inside stored JSON. Receiving allocates local integer identifiers and converts these references before writing. Learner-authored text is preserved verbatim. JSON containing converted identifiers is serialized consistently, while JSON without converted identifiers keeps its original source spelling. An unresolved integer reference is an explicit export error. Integer provenance is not inferred from equal row numbers on another installation.

Export establishes its initial base once. Subsequent exports update `last_export` (`id`, `assets`) without acknowledging those edits on behalf of another installation. `inspect_exchange(pool, workspace, source)` is read-only, including when no installation/course synchronization metadata exists. It returns `course`, `local`, `incoming`, `base`, table inventory, per-asset `errors`, the `plan` (its `changes`, `outgoing`, `conflicts`, `unchanged`), and `association_required`. Unknown target columns and mismatched primary keys are invalid assets, not executable schema migrations.

The common base is this installation's own acknowledgement record: it advances only when a unit is received, never when the same course is exported again. A package's `base` is a witness, not an authority — an asset it calls shared whose local content differs from a value this side never acknowledged is reported as `baseline_mismatch` instead of being guessed. Independent valid units still complete.

`apply_exchange(pool, workspace, inspection, choices)` writes the incoming units of one inspection, and every unit commits on its own: record mappings and the acknowledgement are written before the commit they describe, so a retry after an interruption sees either both or neither and never duplicates an accepted fact. `choices` accepts `side` (`local` / `incoming`), per-identity `items`, and `associate` for a package from a different course lineage; an unresolved conflict returns status `conflict` with no write for that identity. A package received into a course with no local data keeps the package's course origin.

An `execution` unit rebuilds the local active run or the Paper's parked checkpoint from its own header and all items known for it: incoming items replace their positions, unchanged local items are kept, drafts and their sequences are restored, and the other representation of the same execution is cleared. An `execution_item` unit alone patches that position. A Paper generation tombstone only retires a run of an older generation, so a cleared execution cannot come back. A missing envelope is never a deletion; only an explicit `deleted` envelope is.

Receiving keeps the consequences its own writers own instead of copying fields. An imported question edit runs through the Paper-progress update wrapper: the readable revision counts up, a changed content axis clears the whole difficulty rating group, and the affected local drafts reset exactly as an edit made here does. Imported deletions of a question or knowledge point reuse the same deletion path, so a question leaves its Papers and a knowledge point takes its cards, questions, relations and signals; queued Paper file writes are flushed after the units commit. A `part_grading_jobs` row that is still `pending` or `running` is refused — an import never dispatches a Provider job — while `completed` / `failed` rows are carried as history. Import never dispatches a Provider job.

Within an existing package, unchanged envelopes reuse the paths already published by its manifest. Changed envelopes publish new generation paths before the manifest is replaced. After successful manifest publication, obsolete previously listed envelope files are removed. Cleanup only touches paths explicitly owned by the preceding manifest. Publication failure preserves the preceding manifest and all of its referenced files. An export reports written/reused envelope counts, whether the manifest itself changed, and any cleanup errors, and does not claim complete success if cleanup failed. An unchanged projection keeps its export generation, so a repeated export of identical content produces no new package commit.

`files/<workspace-relative path>` holds a plain copy of every managed file asset, and `handoff.md` holds the Tutor-readable digest: goals, the learning-file and Paper index, the current or parked teaching position, the unanswered items, and every recorded attempt with its original answer, verdict and chosen options. Both are views of the package, never extra assets and never written into the workspace. When a readable copy disagrees with its envelope, reading the package takes the readable copy as that asset's content — that is how a Tutor-edited file becomes receivable; envelopes stay the exchange format, and a readable copy without an envelope cannot create or delete an asset.

### Course sync CLI receipt (WP01 in progress)

`lesson-kit course-sync <workspace> export|receive|check|sync|status|schedule` and `course-sync --all-configured sync` print one JSON receipt. Its top-level `status` is `success`, `partial`, `conflict` or `failed`; it carries the course origin, the unit counts, the operation identity (`receive-…` / `sync-…`), the per-unit `applied` / `kept` / `failed` outcomes, and separate `local` and `remote` results — a Git publication failure is reported without claiming remote success. `check` is read-only. A conflict needs one side (`--keep local|incoming`) or per-identity `--choices <file>`; `--associate` accepts a package from another course lineage. Exit code 0 means complete success, 2 an input or format error, 3 a conflict still needing a side, 4 partial completion or transport failure, with 2 taking precedence over 3 over 4. Each course keeps only its latest complete receipt in `.lessonkit/course-sync/last-receipt.json`. An unresolved conflict set is announced once (`.lessonkit/course-sync/last-notice.json` dedupes it). `schedule install|enable|disable|remove` manages one Windows hourly task that runs `course-sync --all-configured sync`; it never installs, enables or removes anything without the explicit action. A receipt is a report, never a substitute for the applied unit identities.

### Requested Git transport (WP01 in progress)

`bridge.git_sync.inspect_repository(repo, branch, remote='origin')` reads branch/index/worktree facts. `fetch_remote` fetches the configured branch into `refs/lessonkit/remote/<branch>` without changing the checked-out branch, index or worktree. `read_remote_files(repo, commit, paths)` returns exact `files` bytes and a `missing` list at a verified commit. Missing remote paths do not authorize entity deletion.

`publish(repo, branch, managed_paths, remote='origin', message=...)` requires the configured branch to be checked out and rejects pre-existing unrelated staged files. Both staging and committing are path-limited, and Git pathspec interpretation is literal. No-change publication creates no commit. Push uses the ordinary branch refspec and reports remote success only after reading back the matching remote commit. Rejection preserves the local commit. Returned `local` and `remote` results remain separate. The CLI owns overall receipt/status/exit-code composition. These functions run argument arrays with explicit repository cwd, disable interactive Git credential prompts, sanitize URL credentials, and do not choose content winners or rewrite user branches.

### Unfinished execution projection (WP01 in progress)

The v1 kinds `execution` and `execution_item` project existing active or parked execution state in the same portable form. `execution` content carries the stable execution reference, Paper identity/generation and existing execution policy fields. Each `execution_item` has a separate identity per execution/position and carries the item, draft, reveal facts, attempt reference and content revision. Cursor, updated time, draft sequence and active selection are transport/presentation metadata outside semantic comparison. Original answer text and draft values are preserved. An item's dependency includes its execution header, and the header references the Paper file and durable execution identity.

The raw active singleton/items are represented by these assets rather than duplicated as competing row assets. A parked `paper_state.checkpoint_json` is similarly split, while the Paper's generation remains a row asset. Exported generation increases explicitly tombstone prior execution assets for that Paper, so a clear operation cannot be interpreted as a merely missing file or revive an older draft. Receiving reconstructs the normal checkpoint representation and must validate generation before publishing.

### WP01 receive checkpoint persistence

`course_sync_checkpoint.state_json` and per-asset `course_sync_units` overrides are the authoritative local receive checkpoint after initialization; `.lessonkit/course-sync/state.json` is a readable copy and legacy starting point. The checkpoint stores course identity, source mappings and acknowledged projections. Each incoming database unit commits only its new mappings and acknowledgements with its rows. Whole-state compaction is transactional at operation boundaries. These local tables never appear in exchange assets or manifests.

A file unit commits a validated `pending_json` publication intent before atomic replacement/deletion, and clears the intent only after publication. An interruption can safely repeat publication. An unwritable file remains pending and is reported as partial while independent units proceed. Check remains read-only, projecting the committed intent and reporting pending publication; modifying exchanges retry it. Sidecar copy failure cannot erase committed record identities or create duplicate history on retry. Missing sidecar files do not authorize a course-lineage change.

### WP01 Git publication and failure receipts

A reception with unresolved conflicts, rejected assets or incomplete dependencies may commit independent valid local units, but does not export over or publish the remote package. The receipt distinguishes local progress from `remote.status=not_published`. Transport failure retains a latest receipt and exit 4, and hourly iteration proceeds with other configured courses. Publication stages current envelopes, readable `files/` copies, handoff and deletion of previously tracked managed paths only.

Remote materialization includes optional readable copies, so an external Tutor can return changes committed only under `files/`. A completed reception advances media ancestry with Git's fast-forward-only operation before export. True Git ancestry divergence remains explicit; there is no reset, force push or implicit course content merge. Notification text travels as process data, and resolved conflicts re-arm notification for later recurrence.

WP01 inspection carries a connection-local SQLite change guard. Apply checks it before writes and within each unit's write transaction; intervening local edits cannot be overwritten by an inspection snapshot. A stale inspection requires a fresh check, preserving already committed independent units. An unresolved file intent blocks newer changes to the same asset while other identities proceed; there is never more than one durable publication intent per identity. Malformed execution items are isolated during package validation, including content-less tombstones that the execution writer cannot represent.

Received file identities remain managed on subsequent exports without copying device-specific media configuration. Existing source bytes are read from the acknowledged relative path, and an acknowledged explicit tombstone is re-emitted while its entity is absent. Missing live assets are reported before export publication; absence never manufactures a tombstone. This closes multi-hop attachment and explicit-deletion propagation, while local hard-delete writers still need explicit deletion recording under the content-operations reconciliation.
