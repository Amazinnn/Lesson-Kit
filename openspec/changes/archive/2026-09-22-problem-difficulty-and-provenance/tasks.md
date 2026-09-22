# Tasks

## 1. Contract and glossary

- [x] 1.1 Define provenance, objective difficulty, and learner difficulty terms.
- [x] 1.2 Add capability deltas and strict validation.

## 2. Domain and schema

- [x] 2.1 Add failing Decimal score and completeness tests, then the pure scorer.
- [x] 2.2 Add failing migration tests, then rebuild `problems` with provenance and vector fields.
- [x] 2.3 Preserve foreign keys/indexes and pass `foreign_key_check`.

## 3. Explicit rating

- [x] 3.1 Add failing check/apply, atomicity, overwrite, and invalidation tests.
- [x] 3.2 Add the Data transaction and `lesson-kit difficulty` CLI.
- [x] 3.3 Remove difficulty/basis from content ingest and Agent generation prompts.

## 4. Provenance and selection

- [x] 4.1 Require provenance on Agent content and define derived source groups.
- [x] 4.2 Add failing source/difficulty filter and balanced-selection tests.
- [x] 4.3 Add CLI/API arguments and hidden plan distribution/mix.

## 5. Verification

- [x] 5.1 Recreate or migrate only the disposable dmath test pool.
- [x] 5.2 Run all repository checks and archive the change.

> Acceptance update (2026-09-22): a temporary copy of `pool/dmath.db` migrated
> twice with 345 problems, 3 progress rows, and 3 attempts preserved; provenance
> became 303 `source_problem` plus 42 `generated_grounded`, difficulty stayed
> wholly unrated, `foreign_key_check` was empty, and `integrity_check` was `ok`.
> Full checks after the latest acceptance fixes and archive remain for the next
> Agent. Never run this migration against an external or real learner pool.
>
> Acceptance (2026-09-22, next Agent): a second disposable copy was migrated
> through the public `pool/scripts/migrate-progress.py` entry point — run 1
> applied `problems.provenance-difficulty-v1` + `flash_cards.directions`, run 2
> reported "No migration needed". Invariants repeated exactly (345 / 3 / 3,
> 303 + 42 provenance, 0 rated, empty `foreign_key_check`, `integrity_check` ok,
> four problem indexes intact), which confirms the `foreign_keys=ON`
> transaction-order fix in `ensure_workbench_schema`. Repository checks on the
> final tree: pytest 495 / Node 109 / compileall / strict 11 / doctor / both
> guards PASS.
>
> Real-Pi finding (fixed here): `lesson-kit pull <workspace>` with no `--kp`
> crashed — `Pool.problems_for_kps` built `WHERE ()` from an empty id list and
> `cmd_pull` passed the empty `--kp` default straight through. `problems_for_kps`
> and its `cards_for_kps` sibling now return `[]` for an empty id list, and
> `cmd_pull` derives the active-lens KPs (`Pool.scope_prefix()`) when `--kp` is
> absent; two CLI tests cover both. The defect pre-dates this change
> (`7d1b081`), so it is a fix, not a regression.
