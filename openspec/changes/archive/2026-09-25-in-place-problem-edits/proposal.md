## Why

The learner's two real courses hold 204 and 728 problems, and every one of the
728 that is not already an objective item is unpractisable in 判断/小测. The only
way to fix a problem's attributes was to delete it and re-import it, which for a
whole course means: re-author the manifest, re-upload the figures, re-check
everything, and lose nothing only if the source files are still at hand. That is
the workload they named: 「删除重导的工作量实在是太大了」.

Three measurements shaped this change (all read-only, against a copy or with
`mode=ro`):

- the readable id carries **no read-time meaning** (`pull` decides by
  `practice_modes`, the practice page by `micro_quiz`), so an existing row can be
  converted in place and every attempt, rating, and schedule stays attached;
- the 200-character stem bound was the real blocker for their 单选题 — 126 of the
  133 option-bearing candidates in one pool exceed it, and the pool's longest
  stem is 5,273 characters;
- `data update` silently **dropped unknown field names**, which is exactly the
  wrong failure mode for a bulk edit, and `data delete` reported success for a
  problem that never existed.

## What Changes

- **The micro-quiz stem bound goes from 200 to 800 characters.** Long 判断题 and
  单选题 are normal content; the bound is a sanity ceiling now, not a statement
  that objective items must be short.
- **`data update problem` gains the attributes that matter**: `practice_modes`,
  the whole `micro_quiz` payload, `source_evidence`, `source_answer`, and
  `solution_origin`, on top of the descriptive fields it already had. Unknown
  field names and difficulty fields are refused with the writable list (or the
  `lesson-kit difficulty` pointer) instead of being dropped. An id cannot be
  renamed, a mode follows the payload unless the caller declares it, and clearing
  the payload returns the item to 综合题.
- **A new bulk channel, `problem-patch`**: one manifest edits many existing rows
  through one prevalidation, one recoverable backup, one transaction, one batch
  id, itemized errors, and **each row's previous values**, so
  `ingest rollback --batch` restores the old values instead of deleting rows —
  an edit and its reversal both leave learning records alone. The Agent can
  submit it as a governed action, but only on an explicit instruction.
- **Options can be lifted out of an old stem.** A patch may rewrite
  `problem_text` and put the option block into `options` verbatim, which is what
  turns a question-bank 单选题 into a 小测 item; nothing is fabricated, and the
  previous text is in the batch snapshot.
- **Two honesty fixes**: `data delete` on an unknown id now fails instead of
  claiming success, and `--input` missing gives a clean error instead of a
  traceback.

## Capabilities

### Modified Capabilities

- `micro-quiz-content`: the stem bound (800 characters) and in-place conversion
  of an existing problem into a micro quiz.
- `workbench-content-governance`: the in-place patch contract (previous-value
  rollback, all-or-nothing bulk edit, refusal of unknown fields).
- `ai-teacher-bridge`: the `problem-patch` action, still gated on an explicit
  learner instruction, and what the contract tells the Agent about it.

## Impact

`workbench/data/content.py` (shared patch planning plus the single-row writer),
`workbench/ingest/__init__.py` (gate, apply, rollback, recipe, `apply_batch`),
`workbench/domain/micro_quiz.py` (the bound), `workbench/cli/main.py` (recipe
choice, input guard), `workbench/bridge/conversations.py` (action kind, contract
text, outcome labels), and docs (FILE_CONTRACT, GLOSSARY, PRODUCT-MANUAL,
REQUIREMENTS, ARCHITECTURE, ACTION-GRAPH). No schema change, no id change, no
automatic edit, and the real pools are only read: the acceptance runs on copies.
