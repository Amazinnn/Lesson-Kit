## Why

A content bundle is pinned to one chapter: the gate builds `scope =
"{course}-{chapter}"` and every allocated id, every figure destination, and the
figure root at apply time come from that one value. A reply that would import two
chapters therefore cannot be honoured, and the action parser makes it worse: it
applies the first matching content block and strips the rest from the mirrored
answer, so a three-chapter reply writes one chapter and says nothing about the
other two. The learner's request "import chapters 12–14" needs three turns, and
the two that were skipped look like the agent simply stopped.

## What Changes

- Each knowledge point, problem, and flash card in a bundle MAY declare its own
  `chapter`; the bundle-level `chapter` becomes the default for items that omit
  it, and an item that can be assigned to no chapter is refused with its reason.
  Chapter assignment is still mandatory for every item — it is only allowed to
  vary within one bundle.
- Everything derived from an item uses that item's chapter: allocated ids,
  figure logical paths and destination directories, micro-quiz ids, and the
  duplicate check.
- One bundle still validates and commits as one transaction behind one backup,
  and now lands as **one batch per chapter**, in chapter order. Each batch is
  independently rollbackable, so importing three chapters and undoing only the
  wrong one both work.
- Every content block in a provider reply is applied, in order, each as its own
  action and its own batch set; the result cards list each batch with its own
  rollback state. Intent-gated blocks (practice selection, goal form) keep their
  single-match, intent-gated behavior.
- The teacher contract states that one manifest may span chapters and that every
  block in a reply is honoured.

## Capabilities

### Modified Capabilities

- `workbench-content-governance`: the staged content bundle accepts per-item
  chapters and records one batch per chapter; the batch registry and rollback
  gain the per-chapter granularity that follows.
- `ai-teacher-bridge`: the check-ingest action applies every content block of a
  reply instead of the first, and reports one batch per chapter.

## Impact

Additive manifest field, additive batch granularity, additive result and mirror
shape (the legacy single-batch fields stay for a single-chapter bundle), plus the
result card rendering each batch. Existing single-chapter manifests, the CLI
batch listing, the rollback endpoint, and every stored row are unchanged.
