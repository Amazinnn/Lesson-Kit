## Context

`micro_quiz` is a JSON payload stored on `problems`. `error_reason` is not a
SQLite column. `workbench/domain/micro_quiz.py` requires it whenever an answer
key is present, `FILE_CONTRACT.md` documents the same rule, `paper-practice.js`
renders it as「判定依据」, and the bundled content-generation skill plus the
pool-pipeline prompt/preflight also require it.

The owner considers it a duplicate of the answer/explanation and wants it gone.

## Decisions

### D-1: Remove the requirement, keep old payloads readable

`validate_payload` will no longer require `error_reason`. It also does not reject
unknown keys, so existing payloads that still carry `error_reason` continue to
load. The reader ignores the field; no SQLite migration or JSON rewrite is part
of this change.

Rejected: a physical migration that strips the key from every `micro_quiz` row.
It is a content patch with rollback/audit concerns, not needed for the contract
removal.

### D-2: Keep `answer_key` and `solution`

The answer key remains the machine-grading fact, and `solution` remains the
written explanation shown in the reveal. Removing `error_reason` removes only the
third, separate「判定依据」section; it does not remove the answer or the solution.

### D-3: Update generation prompts at the source

The bundled `source-bounded-learning-drill` skill and the pool-pipeline prompt
and preflight are part of the content-generation contract. If they keep requiring
`error_reason`, new content will keep producing a field the product no longer
uses. They are updated in the same change.

### D-4: No UI fallback or synthesized reason

The answer reveal simply omits the section. It does not derive a replacement
reason from the answer key, solution, or distractor text.

## Risks

- Existing content loses one visible explanation block. The answer key and full
  solution remain; this is the intended trade-off.
- Third-party or remembered manifests that still send `error_reason` remain
  accepted, because the validator ignores extra payload keys. The field is
  simply not used.
- Old tests and fixtures that assert the field is required must be updated; that
  is part of the same change.
