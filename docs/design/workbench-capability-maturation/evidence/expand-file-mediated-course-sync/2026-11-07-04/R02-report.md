# R02 — Read-only reference audit: execution / grading / idempotency tables

Scope: `attempt_operations`, `practice_request_operations`, `part_attempt_context`,
`part_grading_revisions`, `part_grading_jobs`, `practice_runs`, `paper_state`.
No source edits. No completion claim. Target file `workbench/data/course_sync.py` was read, not touched.

## 0. Baseline already present in course_sync.py (do not re-derive)

| Anchor | Lines | Content |
|---|---|---|
| `TABLES` | 26–36 | all 7 tables already listed |
| `IDENTITY_TABLES` | 37–38 | `problem_attempts`, `feedback_events`, `practice_runs`, `practice_execution_ids`, `content_mirror_log`, `question_progress` |
| `INTEGER_REFERENCES` | 39 | `attempt_id→problem_attempts`, `execution_id→practice_execution_ids` |
| `REFERENCE_JSON_FIELDS` | 40–46 | `practice_runs.items_json`, `paper_state.checkpoint_json`, `attempt_operations.{result,pre_state,post_state}`, `practice_request_operations.{payload,result}`, `part_grading_revisions.{request_json,payload_json}` |
| export remap | 245–302 | `_portable_integer_references`; `nested()` 261–274; opaque-preserve key set 269; PK re-key 294–301 |
| import remap | 713–749 | `_local_row` / `_local_nested` |
| execution split | 375–443 | `_execution_projection` → `execution/<id>` + `execution/<id>/item/<pos>` |
| execution write | 886–903, 928–936, 945–977, 990–1060 | `_write_execution`, `_item_record`, `_write_execution_item`, `_write_active`, `_write_checkpoint` |
| job redispatch guard | 1101–1102 | `part_grading_jobs` pending/running rejected on import |

## 1. Per-table reference map

`int` = persistent integer identity reference; `tok` = opaque idempotency token (never normalize);
`txt` = learner-authored text/container (verbatim); `snap` = authoring snapshot (verbatim, not learner text);
`job` = provider dispatch state.

### attempt_operations (pool_schema.py:659–678; PK `request_id,problem_id`)
| Field | Kind | Target | Nullable / sentinel | Evidence |
|---|---|---|---|---|
| `request_id` | tok | — | NOT NULL, opaque | writer `attempts._insert_operation` 350–361; replay `_replay` 389–395, `_require_same_batch` 381–386 |
| `problem_id` | — | `problems` (text key) | NOT NULL | 353–361 |
| `attempt_id` | int | `problem_attempts` | NOT NULL | written 356; consumer `linked_operation` 373–378, `correct` 275–280, `get_attempt` 691–705 |
| `kind` | enum | — | `apply`\|`correct` | CHECK 666 |
| `rating` | int? | — | **NULL = ungraded recording** (`UNGRADED_STATUS`, 346–347) | 356 |
| `fingerprint` | hash | embeds `attempt_id` | NOT NULL | built 357 over `{"kind","attempt_id",**item}` |
| `batch_fingerprint` | hash | embeds batch + `attempt_id` | NOT NULL | 217, compared at 382 |
| `result` | int refs + txt | `problem_attempts`, `practice_execution_ids`, `practice_runs` | NOT NULL | nested paths below |
| `pre_state`/`post_state` | ? | — | NOT NULL | written 305/342 via `_snapshot(pool, problem_id, _targets(...))` — **UNVERIFIED** (§5 gap G1) |

Nested `result` paths (built `attempts._effects` 316–343 + `apply` 224–241):
`result.attempt_id` → `problem_attempts` (**remapped** by `nested()`).
`result.paper.execution_id` → `practice_execution_ids` (**remapped**).
`result.paper.run_id` → `practice_runs.id` (**NOT in `INTEGER_REFERENCES` → never remapped; dangling after import**).
`result.paper.previous_states.<problem_id>` = attempt_id (dict key is a problem id, so `nested()` treats the int as a leaf → **not remapped**).
`result.paper.positions.<problem_id>` = presentation index, correctly *not* remapped.
`result.paper_position` = index; `result.paper_action` = `import`\|`rebind`; `result.changes` (learning-effect log) = content.
**Gap G2:** `fingerprint`/`batch_fingerprint` embed the *source* `attempt_id`; after attempt remap a genuine re-send of the same `request_id` re-derives a different batch and raises `ManifestError` at `_require_same_batch` 381–386, and `correct` 271–274 fails the same way.

### practice_request_operations (pool_schema.py:680–691; PK `request_id`)
| Field | Kind | Evidence |
|---|---|---|
| `request_id` | tok | `_save_browser_operation` 676–682; replay compare 663–673 |
| `payload` | tok + int | canonical `json.dumps(..., sort_keys=True, separators=(",",":"))` 646–648. Contains `execution_id`, `position`, `part_id`, `context.{execution_id,paper_id,paper_generation,item_id,content_revision,position}`. **Byte equality is the replay contract (671)** — any rewrite must reproduce the exact separator form (`course_sync.py:293` already does) |
| `result` | int list | `{'attempt_ids':[…],'replay':False}` (`part_practice.submit` 140, `_submit_item` 119) and single-`attempt_id` results (attempts 642). **Gap G3: `attempt_ids` is a list under a non-identity key → `nested()` never remaps it → imported replay cache returns source-local attempt ids** |

### part_attempt_context (pool_schema.py:1034–1036; PK `attempt_id`)
`attempt_id` int → `problem_attempts` (writer `part_practice._submit_item` 110–113; reader `grading_jobs.target` 16–29 joins on it).
`execution_id` int → `practice_execution_ids` (writer 112–113).
`part_json` snap, NOT NULL — the part definition captured at submit time (`id`,`type`,`options`,`answer_key`,`reference_answer`,`reference_reasoning`). Must stay verbatim and must **not** be re-derived from the target's current `problems.parts`: `part_practice.definitions` 10–15 prefers this snapshot precisely so a later question edit cannot rewrite grading evidence. Not in `REFERENCE_JSON_FIELDS` — correct, it holds no int identities. No sentinels.

### part_grading_revisions (pool_schema.py:1028–1033 + part_grading.ensure_schema 47–53; PK `attempt_id,revision`)
`attempt_id` int → `problem_attempts`.
`revision` int, append-only, `1..n`; expected-revision guard `mutate` 119–121.
`operation_id` tok, `NOT NULL UNIQUE` — replay guard 105–110 (`'operation identity conflict'`). Never rewrite.
`request_json` snap+int, NOT NULL — a **JSON array**, not an object: `[attempt_id, problem_id, part_id, content_revision, expected_revision, checked, withdraw]` (101–102). **Gap G4: `nested()` recurses into lists but only remaps dict *keys*; element 0 stays a source-local int, so any later re-derivation of the same `operation_id` mismatches at 105–110.** Element 5 `checked` duplicates `payload_json` and must stay byte-identical.
`payload_json` snap/txt (agent-authored grading), **NULL = withdrawal** (`_decode` 60; `withdrawn` 1). `mutate` 98–99 forbids payload+withdraw together — preserve that invariant on import.
`withdrawn` 0/1 int (`_decode` 62 → bool).
**Gap G5:** `(attempt_id, revision)` PK and `operation_id` UNIQUE collide if both sides independently produced revision 1 for the same attempt.

### part_grading_jobs (pool_schema.py:1037–1041; PK `attempt_id`)
| Field | Kind | Nullable / sentinel | Evidence |
|---|---|---|---|
| `attempt_id` | int → `problem_attempts` | PK | insert `part_practice._submit_item` 116–118; read `grading_jobs.get/target` 16–46 |
| `execution_id` | int → `practice_execution_ids` | NOT NULL | 117–118 |
| `status` | job | `pending`\|`running`\|`completed`\|`failed`, default `pending` | `update` 38–46, `pending` 49–51, `retry` 54–59, `claim_next` 62–71 |
| `error` | job | NULL when no failure; machine-local provider text | `project` 182–189 exposes it to the learner once disclosed |
| `conversation_id`,`turn_id` | job (provider session) | NULL until dispatch | `owns_conversation` 8–13 |
| `updated_at` | local clock | NOT NULL | 41–45 |

### practice_runs (pool_schema.py:736–757 + 1021–1024; PK `id`, identity table)
`id` identity (exported as `practice_runs/<id>`).
`source_kind` CHECK `paper|quick|practice_set|agent` — legacy values retained; `active_practice.replay` 393–402 normalizes semantics on replay, **must not be rewritten on import**.
`source_ref` nullable; `ps-*` = saved Paper (`saved_attempt` 216–226 uses `GLOB 'ps-*'`); deleted Papers keep their ref forever (`practice_sets.py:176`).
`kp_ids_json`, `practice_mode`, `rating_mode`, `status` (`completed|abandoned`), `started_at`, `finished_at`.
`items_json` txt+int, NOT NULL — writer `_archive` 319–366.
`execution_id` int?, **NULL = legacy run with no execution identity** (no DEFAULT; `guard` 161–163 and `saved_attempt` 223 skip NULL). Distinct from `active_practice.execution_id` `NOT NULL DEFAULT 0`.
`paper_generation` int, `NOT NULL DEFAULT 1` — **1 is indistinguishable from a legacy default**.
`reveal_timing` TEXT?, **NULL = presentation policy was never recorded** (comment at pool_schema 1023). Must stay NULL; never coerce to `per_item` (`get_run` 768 only *defaults in memory*).

Nested `items_json[i]`: `position`, `item_type`, `item_id`, `direction`, `state`, `attempt_id` (int → remapped), `content_revision`, and when `reveal_timing` is explicit `draft` + `draft_sequence` (334–336). `draft` holds `stuck`, `reference_viewed`, `answer`, `choices`, `sequence`, `part_definitions` (snap), `parts.<part_id>.{answer,choices,stuck,reference_viewed,sequence,attempt_id}`.
**Gap G6: `draft.parts.<part_id>.attempt_id` is an int identity nested inside the container that `nested()` deliberately preserves whole (`course_sync.py:269`)** → survives import as a dangling source id; `_item_record` 933 remaps only the item-level `attempt_id`.

### paper_state (pool_schema.py:1004; PK `paper_id`)
| Field | Sentinel | Evidence |
|---|---|---|
| `paper_id` | `ps-NNN` text | `park` 93–109, `remove_question` 615–616 |
| `generation` | NOT NULL DEFAULT 1; monotone | `reset` 112–116 (`+1`), `remove_question` 616 (`+1`), `continuation` 568, `guard` 170–174 |
| `checkpoint_json` | **NULL = no parked progress** (also the post-reset state) | writer `park` 107–108 / `bind_attempts` 454–456 / `_write_checkpoint` |
| `pending_json` | **NULL = no pending publication** | `queue_file` 123–128 |
| `pending_delete` | 0/1 | `queue_file` 126–128 |

`pending_json`/`pending_delete` are a **publication intent, not history**: `flush_files` 131–147 will `unlink` or atomically overwrite the local Paper file on the next commit. **Gap G7: they are absent from `REFERENCE_JSON_FIELDS` (they hold no int identities) but importing a source-side intent can delete/overwrite a local saved Paper — they must be forced to the target's inert default (`NULL`, `0`) on import.**

## 2. Checkpoint split for independent per-question merging

`paper_state.checkpoint_json` is one blob per Paper, so cross-machine per-question merge is impossible until it is decomposed. Current `_execution_projection` 375–443 already splits it; the split boundary that must be preserved:

**Execution header (merge unit = whole execution; never merged per question):**
`source_kind`, `source_ref`/`paper_id`, `source_label`, `kp_ids`, `practice_mode`, `rating_mode`, `started_at`, `reveal_timing`, `execution_id` (int → `practice_execution_ids`), `paper_generation`.
Presentation metadata, kept out of the mergeable body (411): `cursor`, `updated_at`, `progress`, `selected`.
Rationale: `execution_id` is a single opaque run identity — two machines' executions cannot share one; `paper_generation` must equal `paper_state.generation` (see §3); `cursor` is derived from item states (`_next_cursor`, `bind_attempts` 452), so merging two cursors is meaningless.

**Per-question item (merge unit = one position):**
`position`, `item_type`, `item_id`, `direction`, `state`, `attempt_id`, `content_revision`, `draft`, `draft_sequence` (enumerated at 325–337 and 928–936; injected `execution_id`/`paper_id`/`paper_generation` at 426–427 are derived, not stored).
Per-item merge rules that must hold, from the writers:
- `state` and `attempt_id` are coupled — `part_practice._submit_item` 121–125 sets both; a merged `answered` with `attempt_id=NULL` is invalid.
- `content_revision` must equal the *target's* `problem_revisions` value (`continuation` 570–573; `reconcile_active` 67–76). Importing a stale revision must reset the item to `pending` with `attempt_id=NULL`, `draft={}`, `draft_sequence=0` — exactly what `_changed` 40–41 does locally.
- `draft_sequence` is monotone per item and is the stale-write fence (`part_practice.save_draft` 70–76). Merge must take `max`, and the *inner* `draft.parts.<part_id>.sequence` must be `max`-merged too, or a legitimate newer draft is rejected as `'stale part draft'`.
- `draft.part_definitions` must travel with the item verbatim (authoring snapshot; see §1).
- `position` is **not** a stable merge key: `remove_question` 618–630 renumbers positions and rescales `cursor`. Merge by `(item_type,item_id)`, then re-derive positions.

## 3. How reset generation prevents revival

- `reset` (112–120): `generation = generation+1`, `checkpoint_json = NULL`, and if the Paper is currently selected the active run is `_delete`d. A parked record from before the reset can therefore never match.
- `continuation` 568 rejects `record.paper_generation != paper_state.generation` → `'旧执行对应的试卷结构版本已过期，不能继续'`.
- `guard` 170–174 rejects a submit whose `context.paper_generation` disagrees with either the record or `paper_state.generation`.
- `remove_question` 616/629 bumps the generation and rewrites `paper_generation` in every surviving snapshot, so membership edits invalidate older snapshots.
- Import side already enforces it: `_write_checkpoint` 1043–1046 raises `'the incoming execution belongs to an older Paper generation'` when local `generation > incoming`; 1053–1055 stores `max(generation, local)`; `_retire_execution` 906–925 only tombstones when `generation > parked.paper_generation`.
**Gap G8 (behaviour question, not schema):** 1045–1046 *raises*, which aborts the whole unit; the same condition locally is a silent non-revival. Decide whether a newer local generation should discard the incoming execution as a tombstone instead of failing the import.

## 4. Can import accidentally redispatch provider work?

- **Blocked:** `_write_unit` 1101–1102 rejects `part_grading_jobs` rows with `status in {pending,running}` — `'a waiting grading job is not dispatched by an import'`. This is the only control that matters for auto-dispatch, because `grading_jobs.pending()` 49–51 (the dispatcher's feed) selects exactly those two states.
- **Still open (G9):** `completed`/`failed` rows import with the source's `conversation_id`/`turn_id`. `owns_conversation` 8–13 then answers *true* on the target, i.e. the other machine's provider session is claimed as a local one. And an imported `failed` row is immediately eligible for `retry` 54–59 (`failed→pending`), which re-dispatches provider work on explicit retry only. Either strip the provider-session pair and keep `status`/`error` as evidence, or import such rows as `failed` with a local reason.
- **No dispatch from other tables:** `part_attempt_context` alone leaves `part_practice.project` 182–189 at `grading_status='not_requested'`; `attempt_operations`/`practice_request_operations` replay paths (`attempts._replay` 389–395, `_browser_replay` 663–673) return cached results and never call a provider.
- **Global stall hazard:** `claim_next` 62–71 returns `None` whenever *any* `running` row exists, so a single imported stale `running` row would freeze all grading forever — another reason 1101–1102 must stay.

## 5. Unresolved evidence gaps

- **G1** `attempt_operations.pre_state`/`post_state`: written via `_snapshot(pool, problem_id, _targets(pool, problem_id))` (attempts.py:305, 342); I did not read `_snapshot`/`_targets`, so whether they embed `attempt_id` or learner text is unverified. They are listed in `REFERENCE_JSON_FIELDS`, which implies the author expected int references there.
- **G10** `workbench/bridge/grading.py:121 dispatch_pending` was not read (inventory-only reference). Whether it dispatches strictly from `grading_jobs.pending()` or also from attempt rows is unverified; if it can dispatch from attempts, §4's guarantee weakens.
- **G11** No verification of how `_local_nested` (713–749) treats a JSON **array** root (`part_grading_revisions.request_json`) — I read `_portable_integer_references.nested` (261–274) but not `_local_nested`'s list branch; G4 is inferred from the export side and should be confirmed against the import side.
- **G12** `tests/workbench/real_pool_conformance.py:35` and `tests/workbench/test_course_sync_receive.py` were not read; existing conformance coverage for these seven tables is unknown, so no claim is made that any of the gaps is currently untested or tested.

## 6. One-line summary of actionable gaps

G2 stale `fingerprint`/`batch_fingerprint` · G3 `practice_request_operations.result.attempt_ids[]` unremapped ·
G4 `part_grading_revisions.request_json[0]` unremapped (breaks `operation_id` replay) ·
G6 `draft.parts.<id>.attempt_id` unremapped · G7 `paper_state.pending_json/pending_delete` intent import ·
G9 imported `conversation_id`/`turn_id` + `failed→pending` retry path · G8 raise-vs-tombstone on newer generation ·
G5 `(attempt_id,revision)`/`operation_id` collision across machines.
