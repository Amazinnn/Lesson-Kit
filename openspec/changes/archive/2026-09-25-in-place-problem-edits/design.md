# Design — In-place problem edits

## What the measurements settled

| Question | Finding | Consequence |
|---|---|---|
| Does the id suffix mean anything at read time? | No: `pull._eligible_for_mode` reads `practice_modes`, the practice page reads `micro_quiz`, `chapters()` only needs one of `kp/prob/mq/fc`, and learning tables key on `item_type` + `item_id` | A converted `-prob-` row works everywhere; keeping the id keeps every attempt, rating, and schedule |
| Why can't their 单选题 be 小测 today? | The micro contract capped the stem at 200 characters; 126 of 133 option-bearing candidates exceed it (max 5,273) | Raise the bound to 800 — a ceiling, not a design statement |
| Is any read-time consistency check violated by a conversion? | None: the `micro_quiz` ↔ `practice_modes` rules live only in the ingest gates, which insert new rows and refuse existing ids | The patch must own the validation itself; nothing else re-checks |
| What is the current failure mode for a wrong field name? | Silently dropped (`EDITABLE_FIELDS` filtering), so a typo returns "success" with nothing changed | Refuse unknown fields and list what is writable |
| Is there a precedent for a rollback-able update? | Yes — `figure-patch` stores a `previous` list in its batch snapshot and `_rollback_figure_patch` writes it back | Reuse exactly that shape for a general problem patch |

## One authority, two entry points

`data.content.plan_problem_patch(row, data, course)` is a pure function over the
decoded current row. It returns the itemized errors, the column values to write,
and whether the difficulty group must be cleared. Both writers go through it:

- `data.update problem` (one row, `lesson-kit data … update problem <id> --input`)
  reads the row from the Pool and executes the assignments;
- `ingest`'s `problem-patch` gate reads the row from its own connection and stores
  the same assignments plus the previous values in the batch snapshot.

Rules it enforces, all in one place:

1. An unknown field name is an error that lists the writable set; a `difficulty*`
   field points at `lesson-kit difficulty`. Nothing is dropped silently.
2. `problem_id` is identity: a patch cannot change it, and a bulk item's id must
   start with the workspace course.
3. `practice_modes` follows `micro_quiz.quiz_type` unless the caller declares it;
   `[]`/`null` is exam-only; a micro/yes-no marking without a payload is refused.
4. A supplied whole payload gets the full micro contract (`validate_payload`);
   the `answer_key` shorthand only checks the key's shape, so filling a key later
   never forces an error reason.
5. Only the parts the patch touches are re-validated (payload shape, one knowledge
   point when it becomes or stays micro, the stem bound when the stem changes,
   the mode marking). Legacy rows therefore stay patchable without their old
   content being re-judged.
6. `kp_ids`/`problem_text`/`solution`/`problem_type` keep their existing rule:
   changing one clears the whole difficulty group. Mode, payload, provenance, and
   answer-key edits do not.

## The bulk channel

`problem-patch` joins the governed kinds, so it rides the existing machinery:

- **Manifest**: `{"kind": "problem-patch", "items": [{"problem_id": …, …}]}`;
  also accepted as an inline content block from the Agent (the wrapper spellings
  already resolved by the bridge).
- **Gate**: every item must name an existing row; ids are unique in the batch;
  the id must carry the workspace course; the plan must produce at least one
  field. Any error fails the whole batch with per-item reasons.
- **Apply**: `_allocate_batch_id` → snapshot (manifest + `previous` per row) →
  `_backup_database` → one `UPDATE` per row inside `BEGIN IMMEDIATE`, verifying
  `rowcount == 1` → `_record_batch`. Counts are `problems` and
  `difficulty_cleared` (rows whose rating actually existed).
- **Rollback**: `rollback_batch` gained a branch that restores the recorded
  values and stamps `rolled_back_at`; it deliberately skips the
  "dependent learning records" blocker, because it deletes nothing. The rows keep
  their original `ingest_batch_id`, so the data tables show the patch's batch as
  a snapshot and the original import's batch as the row's owner.

## CLI shape

`lesson-kit ingest <ws> recipe problem-patch --input <manifest> --output <dir>
[--apply]` reuses the recipe grammar, which already guarantees "no pool write
without `--apply`". Single-row edits stay on `data update problem`, which is the
command the Agent already knows from the answer-key backfill.

## Non-goals and honest limits

- No id changes and no conversions of a micro item back into a formal one beyond
  clearing the payload/marking (the payload is dropped, not rewritten).
- The tool never authors content: the Agent (or the learner) supplies the stem and
  the options; the tool validates and writes. For their pools that means the
  remaining questions still need per-item authoring — the patch removes the
  re-import, not the reading.
- Difficulty stays a separate command; a patch that changes a content axis clears
  the rating group (pre-existing rule) and reports how many ratings that cost.
- No UI editor: the practice page already renders a converted row, and the
  browser keeps its read-only contract.
