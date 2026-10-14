# Git-Authored Content Bundles

Git may carry proposed Lesson-Kit content without becoming a second content
authority. The repository-side input is a complete `content-bundle` manifest;
the SQLite pool remains the canonical runtime source of truth.

## Repository layout

```text
<authored-content-repo>/
├── authored-bundles/<course-id>/<chapter>/<name>.json
├── courses/<course-id>/
│   ├── knowledge/<entity-id>.json
│   ├── problems/<entity-id>.json
│   └── relations/<entity-id>.json
├── figures/<course-id>/...
└── delete-requests/<request-id>.json
```

The two trees have different responsibilities:

- `authored-bundles/` is an input/review surface. A pull request may create a
  new bundle from source material before the local pool has allocated ids.
- `courses/` is the canonical authored-content projection produced from rows
  that already exist in the pool. `lesson-kit mirror` owns that projection.

A file in `authored-bundles/` does not itself create a Lesson-Kit entity.

## Identity rule

A Git-authored bundle uses bundle-local `key` values for new knowledge points,
problems, and flash cards. It MUST omit canonical identity fields:

- `knowledge_points[*].kp_id`
- `problems[*].problem_id`
- `flash_cards[*].card_id`

References inside the bundle may use local keys. The governed ingest gate
resolves those references and allocates readable canonical ids in the selected
course/chapter. This prevents a remote author from racing or spoofing the
pool's id allocator.

Existing canonical entities are still edited through their existing governed
update/mirror paths; a Git-authored bundle is for new content, not identity
replacement.

## Check and apply

Check a reviewed file without writes:

```bash
lesson-kit ingest <workspace> bundle --input authored-bundles/<course>/<chapter>/<name>.json
```

The check opens the existing pool read-only and calls the same complete
`content-bundle` gate used by normal ingest. It performs the existing chapter,
knowledge-point reference, provenance, markup, objective-item, duplicate stem,
figure, and typesetting checks. It does not allocate rows, create batches, or
write a backup.

Apply only after review:

```bash
lesson-kit ingest <workspace> bundle --input authored-bundles/<course>/<chapter>/<name>.json --apply
```

Apply delegates to the existing `apply_batch(..., source="cli")` path. The
bundle is revalidated while holding the write transaction, canonical ids are
allocated by the pool, the recoverable database copy and per-chapter ingest
batches are recorded, figures are copied through the existing figure rules,
and the existing rollback semantics remain unchanged.

`--backup <path>` may override the normal recoverable-copy path when applying.
It is invalid for a read-only check.

## Canonical projection after apply

After a successful apply, `lesson-kit mirror ... push` may export the canonical
rows to `courses/<course-id>/...`. The authored bundle may remain in Git as the
reviewed source proposal and audit trail; it is not synchronized as an entity
mirror and its local keys never become canonical ids.

No staging database, candidate table, promotion state, or alternate mutation
channel is introduced by this workflow. Git clone/pull/commit/push operations
remain outside Lesson-Kit, as they do for the existing mirror command.
