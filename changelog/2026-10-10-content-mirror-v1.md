# Authored-content mirror v1

`lesson-kit mirror` projects governed authored content — knowledge points,
durable problems, and knowledge relations — into a local JSON checkout that Git
can review, while the pool stays the runtime source of truth. The command group
provides `init` (pool-first bootstrap at revision 1), read-only `check`/`status`,
and per-entity `sync` with `--entity` and `--dry-run`. Repository edits flow
through the existing governed content/relation validators, and each entity's
content mutation, mirror-state update, and success-log row commit in one pool
transaction. Revisions are readable integers; no hashes, fingerprints, or Git
object ids are stored. A missing repository file is restored as a forward
revision and never deletes pool content, and `delete-requests/` documents are
validated and reported but never executed. No Git network command runs inside
the mirror path.

## Bootstrap hardening

Independent review reproduced two interruption defects before merge; both are
repaired with focused regressions:

- An interrupted missing-file restoration can be retried: the pool revision and
  restore-log row commit before the JSON file is written, so a ledger failure
  leaves the file missing and the same next revision can be retried.
- `init` now accounts for unreadable repository files: they are reported with
  their path and reason, an entity whose id such a file names is refused a
  canonical file while unrelated entities still bootstrap, and one entity's
  write failure no longer aborts the remaining entities.

## Contracts and documentation

The mirror ledger contract is registered in `docs/DATA_MODEL.md`
(`content_mirror_state` / `content_mirror_log` fields, writer and consumer
boundaries); `FILE_CONTRACT.md` carries the repository layout, envelope,
deletion-request, and unreadable-input contract; `docs/GLOSSARY.md`,
`docs/ARCHITECTURE.md`, `docs/PRODUCT-MANUAL.md`, and the action-graph L0–L4
layers are updated (CLI 顶层命令增至 24, new W9 workflow). The external rollout of real
course content remains open in the `json-content-repository-sync` change.

## Verification

Focused acceptance on the repaired HEAD: the mirror contract suite including the
unreadable-input, write-isolation, convergence, revision-jump, missing-pool-row,
and partial-success regressions, plus the adjacent content-governance and
relation suites — all green; evidence is stored with the PR #110 closeout.
Full repository gates and isolated real-pool acceptance are recorded with the
PR #110 delivery.
