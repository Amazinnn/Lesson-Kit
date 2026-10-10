# Design: JSON content repository sync

## 1. Boundary

The knowledge pool remains the runtime source of truth required by ADR 0009 and the project context. The JSON repository is not a second runtime store. It is a version-controlled authored-content projection that may originate governed edits.

This distinction matters:

```text
web Agent / human
        |
        v
checked-out JSON repository
        |
        | validate + compare + governed mutation
        v
course knowledge pool  <---- workbench/runtime reads
        |
        | authored-field export
        +------------------------> JSON repository
```

Runtime state has only one home: the pool/workspace. Git transports authored content only.

## 2. Repository layout

One repository holds many courses. Local workspace paths are irrelevant.

```text
<repo>/
  repository.json
  courses/
    <course-id>/
      course.json
      knowledge/
        <entity-id>.json
      problems/
        <entity-id>.json
      relations/
        <entity-id>.json
  delete-requests/
    <request-id>.json
```

`course-id` is the existing Course Identifier. File names are conventional for readability; entity identity comes from the JSON envelope. Moving/renaming a file without changing the envelope id does not create a new entity or delete the old one.

The synchronizer scans the supported entity directories under the selected course, including nested folders, plus deletion requests targeting that course. A future Git changed-path optimization may reduce scanning, but paths are never semantic identity.

## 3. Entity envelope

Each entity file is strict JSON:

```json
{
  "schema_version": 1,
  "entity_type": "problem",
  "entity_id": "c04-ch03-prob-017",
  "revision": 4,
  "content": {
    "problem_text": "...",
    "solution": "..."
  }
}
```

Rules:

- `schema_version` is the integer `1`; booleans and non-integer numeric values are rejected.
- `entity_type` is one supported entity kind.
- `entity_id` is immutable and must belong to the selected course.
- `revision` is a positive, monotonically increasing integer managed by synchronization/export tooling; one semantic authored-content generation advances it once.
- `content` contains authored fields only. Unknown fields fail validation; they are never silently dropped.
- Fields stored as JSON arrays or objects retain those JSON types; stringified JSON is rejected.
- JSON is UTF-8 and canonical output uses two-space indentation, `ensure_ascii=false`, sorted envelope/content field order as defined by the writer, and a final newline. Formatting differences alone never create a semantic revision.

No hash, fingerprint, SHA field, or content-derived identifier is used.

## 4. Mirrored projection

V1 mirrors the governed mutable fields already owned by `workbench.data.content` for `kp`, `problem`, and `relation`. Flash-card entities, figure bytes, specialized problem-difficulty fields, and repository-only entity creation are outside v1. The id is carried by the envelope and cannot be patched through `content`.

Database-only columns such as `created_at`, `updated_at`, batch bookkeeping, learner state, attempts, schedules, feedback, signals, and derived/cache values are excluded.

Specialized authored fields that have a separate mutation contract are excluded until a separate approved change routes them through that authority.

## 5. Synchronization state without hashes

The pool receives two additive tables.

`content_mirror_state` records, per `(entity_type, entity_id)`:

- the last synchronized integer `revision`;
- the last synchronized normalized `content` JSON text;
- `updated_at`.

`content_mirror_log` records successful synchronization events with an integer primary key, entity, direction, previous/new revision, action, and timestamp. It stores no Git object id or hash.

The saved normalized content is the common ancestor for comparison. This avoids hashes while permitting exact three-way classification:

```text
baseline = last synchronized content
pool_now = current authored projection
repo_now = entity JSON content
```

## 6. Planning one entity

For a tracked entity:

1. Read baseline revision/content from `content_mirror_state`.
2. Read the current pool projection.
3. Read and validate the JSON entity.
4. Run changed repository values through the existing entity validator and compare its normalized projection, not file bytes. A successful accepted edit rewrites the repository envelope with that normalized projection at the incoming revision.

Classification:

| Pool vs baseline | Repository vs baseline | Result |
|---|---|---|
| same | same | `noop` |
| same | changed, revision = baseline + 1 | `repo_to_pool` |
| changed | same | `pool_to_repo`, writer advances revision by 1 |
| changed | changed, payloads equal and repository revision = baseline + 1 | `recover_converged` |
| changed | changed differently | `conflict` |
| same | missing file | `restore_repo_file`, advancing revision by 1 |
| missing pool row | present/tracked file | `conflict` |

A repository payload changed without the required next revision is invalid. A revision jump greater than one is invalid. A lower revision is stale and refused. These failures never overwrite either side.

For an untracked entity, normal `sync` does not guess which side wins when both sides contain different payloads. Initial alignment is established explicitly by `mirror init`.

## 7. Bootstrap

`lesson-kit mirror <workspace> init --repo <path>` initializes one course projection from the existing pool.

- It resumes per entity: entities with existing mirror state are skipped as `already_tracked` and uninitialized entities continue.
- It writes one JSON file per supported pool entity at revision 1.
- It records the same normalized content and revision 1 in mirror state.
- If a valid file with the same embedded identity exists anywhere under that entity directory, initialization adopts it when revision 1 content matches, regardless of its filename or nested location.
- If the canonical target exists with a different embedded identity, initialization refuses that entity rather than overwriting it.
- If a same-identity file is duplicated, initialization refuses that entity.
- The operation is per-entity: successful entities remain initialized if a later entity fails, and rerunning resumes the rest.

This makes the first synchronization deterministic for the existing `c02`/`c04` pools instead of asking the tool to infer ancestry from two independently populated stores.

## 8. Per-entity atomicity and partial success

The transaction boundary is one entity, not one Git commit, folder, course, or batch.

For repository-to-pool changes, validation happens before the transaction. The content mutation, mirror-state update, and success-log row are committed in one pool transaction. Existing content writers participate in an enclosing `Pool.transaction`; a validation, mutation, or ledger error rolls back the content and mirror state together.

The normalized JSON envelope is written before the pool transaction commits. If the transaction fails, the next run still sees the same incoming revision and can retry it; a failed envelope write rolls back the pool transaction.

For a missing-file restoration, the pool revision and restore-log row are committed before writing the JSON file. If the ledger write fails, the file stays missing and the prior revision remains, so the same next revision can be retried. This ordering does not permit an arbitrary unchanged file to advance its revision.

For pool-to-repository changes, the JSON writer writes a temporary sibling file and replaces the target. Mirror state is advanced only with a recoverable ordering: any crash leaves either the old state/file or a pair that the next comparison can classify as `recover_converged`/stale and repair without content loss.

A run returns counts and per-entity results: `applied`, `exported`, `restored`, `recovered`, `noop`, `conflict`, and `invalid`. One entity failure does not roll back prior successful entities. Since v1 refuses repository-only entity creation, it does not create or defer references to new entities.

## 9. Deletion behavior

Deletion is intentionally asymmetric for safety.

- Removing an entity JSON file is never interpreted as deletion from the pool.
- A tracked missing file is restored from the pool as a new revision.
- `delete-requests/*.json` may name an entity and a reason. The synchronizer validates and reports the request but has no code path that calls content deletion because of it.
- Existing local/manual delete capabilities remain outside this Git relay. If the pool row disappears, synchronization reports a conflict and requires an explicit local decision.

Thus a mistaken Git deletion cannot destroy learning content or its attached runtime history.

## 10. CLI

V1 surface:

```text
lesson-kit mirror <workspace> init  --repo PATH [--entity ID]
lesson-kit mirror <workspace> check --repo PATH [--entity ID]
lesson-kit mirror <workspace> sync  --repo PATH [--entity ID] [--dry-run]
lesson-kit mirror <workspace> status --repo PATH [--entity ID]
```

- `init`: pool -> repository baseline.
- `check`: parse/validate repository entities and deletion requests; write nothing.
- `status`: classify differences; write nothing.
- `sync --dry-run`: same plan/report as sync, write nothing.
- `sync`: apply/export independent entity operations.

The command operates on a local repository checkout only. It does not run `git pull`, `git commit`, or `git push`; Git authentication/transport stays decoupled from Lesson Kit content semantics.

## 11. Why JSON instead of Markdown

The requested workflow performs exact field edits. JSON gives deterministic field addressing and validation without regex/front-matter parsing, carries Markdown/LaTeX text as ordinary string values, and produces reviewable Git diffs. Strict JSON (not JSONC) keeps one parser contract.

## 12. Real-workspace compatibility

The design intentionally ignores course-workspace layout beyond the registered knowledge pool. The two audited course shapes validate the boundary:

- a mature course with a large mixture of ingest/jobs/figures/intermediate/repair assets;
- a lower-quality course with substantially more intermediate files, scripts, images, backups, and historical batches while its pool still has consistent entity references.

Neither workspace is mirrored. Both reduce to the same normalized per-entity JSON protocol because course placement and production debris are out of scope.
