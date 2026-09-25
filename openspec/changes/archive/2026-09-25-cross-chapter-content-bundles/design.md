# Design — Content bundles that span chapters

## Where the one-chapter limit actually lives

Three places read one chapter value, and none of them is the rollback:

| Site | Use |
|---|---|
| `ingest._gate_content_bundle` | `scope = f"{course}-{bundle_chapter}"` → the prefix for every allocated id |
| `ingest._plan_bundle_figures` | the figure's logical path `{course}/{chapter}/{name}` |
| `ingest._apply_content_bundle` | the figures root `.lessonkit/figures/{course}/{chapter}` |

The rollback path (`_rollback_content_bundle`) deletes by `ingest_batch_id` and
then removes the figure files that batch recorded and that nothing references
any more. It has no chapter assumption at all, so per-chapter batches need no new
rollback machinery — and removing rollback would have bought no freedom here, it
would only have removed the undo.

A latent bug follows from the same reading: an explicitly named id only has to
start with the course prefix, so a chapter-14 problem inside a chapter-12 bundle
was accepted and its figures landed under `figures/{course}/ch12/`. Per-item
chapters remove that mismatch rather than papering over it.

## Item chapters

```
{
  "kind": "content-bundle",
  "chapter": "ch12",                     # optional default for items that omit it
  "knowledge_points": [{"key": "k1", "chapter": "ch12", "knowledge_item": "…"}],
  "problems": [{"key": "p1", "chapter": "ch13", "problem_text": "…", "kp_ids": ["k1"]}]
}
```

Resolution order per item: the item's own `chapter` → the bundle's `chapter` →
the workspace's active chapter lens (today's fallback). A value that is present
must be a lowercase ASCII chapter identifier; an item that ends up with no
chapter is refused with its label, so the mapping "which content belongs to which
chapter" stays mandatory and explicit.

One bundle therefore carries at most one chapter per item and any number of
chapters overall. Ids stay readable and chapter-scoped
(`c01-ch13-prob-004`), and allocation continues per chapter prefix, so a bundle
touching two chapters never produces a ch12 id for ch13 content.

## One bundle, one transaction, one batch per chapter

The bundle is still validated whole, committed in one transaction, and preceded
by one recoverable backup: one invalid item still writes nothing at all. What
changes is what gets recorded — the plans are grouped by chapter in chapter
order, and each group allocates its own batch id, writes its own manifest
snapshot (with that group's `_applied` bookkeeping), and is recorded in
`ingest_batches` with its own counts.

Consequences:

- rollback works per chapter, on the existing endpoint and CLI command, with no
  API change: `batch-007` can be undone while `batch-008` from the same import
  stays;
- a rolled-back chapter no longer blocks re-importing that chapter, because its
  ids are gone;
- the backup stays one file per import, which is what a pool-level recovery needs.

The result carries `batches: [{batch_id, chapter, counts, origins}…]`. For a
single-chapter bundle the legacy fields (`batch_id`, `counts`, `origins`) are
also present, so existing consumers and the single-chapter card keep working.

## Every content block is applied

`_extract_action` already walks every block; it now returns the list of content
actions it recognised instead of the first one, and the caller applies each in
order. Each action keeps its own all-or-nothing validation and its own batch set,
so one bad block fails alone with itemized reasons and does not take the others
down. Intent-gated blocks (practice selection, goal form) keep their existing
single-match semantics, and a reply whose blocks match no contract still records
the disclosure instead of claiming a write.

The turn and the mirror carry `actions` (the list); `action` remains the single
element when exactly one was applied, which is what the existing tests, the
restored mirror, and the single-card path read.

## Result cards

The card renders one row per batch — batch id, chapter, asset counts, and its own
rollback button — and re-checks each batch's current state when a conversation is
reopened, so an already rolled-back chapter shows as such while its sibling stays
rollbackable. The rollback call is the existing `POST /ingest/rollback` with one
batch id.

## Compatibility and non-goals

- A manifest written before this change (bundle-level chapter, no item chapters)
  behaves exactly as it did and still produces one batch.
- The legacy patch channels (`micro-quiz-patch`, `flash-card-patch`) keep their
  current single-batch behavior: their ids are explicit, so they already accept
  several chapters, and they are documented as the compatibility path.
- Non-goals: per-chapter backups (one import is one recovery point), keeping a
  chapter's ids reserved after a rollback, and any change to how the learner
  selects a chapter for practice.
