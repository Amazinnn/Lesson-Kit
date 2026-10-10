# Tasks

## 1. Contract and architecture

- [x] 1.1 Audit the real `c02` and `c04` workspace shapes and explicitly reject whole-workspace Git mirroring.
- [x] 1.2 Define one-repository/many-course layout, one-entity JSON envelope, stable id semantics, integer revision protocol, and no-hash comparison.
- [x] 1.3 Specify the runtime boundary: pool remains runtime source of truth; JSON is an equally editable authored-content projection only.
- [x] 1.4 Specify per-entity atomicity, partial course success, resumability, and non-executing deletion requests.
- [x] 1.5 Record ADR 0024 and update the architecture/manual/action documentation on delivery.
- [x] 1.6 Add the strict entity/deletion-request contract to `FILE_CONTRACT.md` after implementation fixtures prove the exact fields.

## 2. Additive pool state

- [x] 2.1 Add idempotent `content_mirror_state` and `content_mirror_log` tables through `pool/scripts/pool_schema.py`.
- [x] 2.2 Ensure old fixture pools acquire the tables through `ensure_workbench_schema` with no destructive migration.
- [x] 2.3 Add tests proving schema migration is repeatable and stores no hashes/fingerprints/Git object ids.

## 3. Entity JSON implementation

- [x] 3.1 Add a stdlib-only parser/writer for schema version 1 entity envelopes.
- [x] 3.2 Project only governed authored fields for `kp`, `problem`, and `relation`; exclude timestamps/runtime/learning state.
- [x] 3.3 Validate immutable ids, course prefix, entity type, revision, unknown fields, duplicate ids, and path-independent identity.
- [x] 3.4 Write canonical UTF-8 JSON with stable formatting and final newline.
- [x] 3.5 Add valid/invalid golden fixture coverage including Markdown/LaTeX strings stored inside JSON.

## 4. Synchronization engine

- [x] 4.1 Implement explicit pool-first bootstrap at revision 1, resumable one entity at a time.
- [x] 4.2 Implement three-way planning from remembered normalized content, current pool projection, and current JSON content.
- [x] 4.3 Implement `repo_to_pool`, `pool_to_repo`, `restore_repo_file`, `recover_converged`, `noop`, `invalid`, and `conflict` outcomes without hashes.
- [x] 4.4 Route repository mutations through existing content/relation validators and refuse unsupported specialized fields rather than bypassing their contracts.
- [x] 4.5 Confirm repository-only entity creation is refused in v1, so creating or deferring references to new entities is outside this change.
- [x] 4.6 Store one success-log row with each successful semantic revision and prove retry idempotency after simulated interruption.
- [x] 4.7 Validate/report deletion requests while guaranteeing that mirror code cannot call content deletion because of a repository request or missing file.

## 5. CLI

- [x] 5.1 Add `lesson-kit mirror <workspace> init --repo PATH [--entity ID]`.
- [x] 5.2 Add read-only `check` and `status`.
- [x] 5.3 Add `sync [--dry-run] [--entity ID]` with structured JSON report and exit 2 for conflicts/invalid entities while preserving successful siblings.
- [x] 5.4 Confirm no mirror command invokes Git network or authentication commands.

## 6. Verification

- [x] 6.1 Unit-test bootstrap, unchanged state, repository edit, pool edit, same-content convergence, stale/jumped revision, two-sided conflict, missing file restoration, missing pool row, and partial success.
- [x] 6.2 Confirm repository-only entity creation is refused by the focused v1 test; no cross-reference deferral fixture applies.
- [x] 6.3 Add a deletion-request fixture and assert the target row plus runtime history remain unchanged.
- [x] 6.4 Add round-trip tests: pool -> JSON -> edited JSON -> pool -> JSON preserves the supported authored projection exactly.
- [x] 6.5 Run `python -m pytest tests -q`.
- [x] 6.6 Run `python -m compileall -q lessonkit.py workbench pipeline pool tests`.
- [x] 6.7 Run `openspec validate --specs --strict`.
- [x] 6.8 Run the repository extract-problems guard required by `AGENTS.md`.

## 7. Content repository rollout

- [ ] 7.1 Replace the provisional `entities/` layout in `Lesson-Kit-Content` with the proven `courses/<course-id>/{knowledge,problems,relations}/` contract.
- [ ] 7.2 Add `course.json` examples and deletion-request examples only after the parser fixtures are green.
- [ ] 7.3 Bootstrap one real well-formed course and one historically messy course as acceptance samples without copying their workspace debris.
