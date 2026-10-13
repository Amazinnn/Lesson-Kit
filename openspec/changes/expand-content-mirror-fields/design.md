## Context

See `proposal.md` for motivation and `specs/workbench-content-governance/spec.md` for the observable contract. `content_mirror` already projects the extended fields, but it imports difficulty rules from Domain, duplicates their computation, and treats absent schema columns as if they existed during stale-rating clearing. `figure_mirror` owns the existing pure logical-path grammar, and `data.difficulty.check` is the public zero-write authority for complete ratings.

## Goals / Non-Goals

**Goals:**

- Make the mirror plan the shared preflight for pool and repository figure references and difficulty edits.
- Reuse existing Data validation and preserve the current per-entity transaction, state, and log paths.
- Adopt only a complete, next-revision projection that converges with the pool.

**Non-Goals:**

- Change binary figure copying, path naming, repository layout, JSON schema version, pool schema, or CLI commands.
- Rework other Data-to-Domain imports or the content update architecture.

## Decisions

1. **Share a small pure figure-reference validator from `figure_mirror`.** It will call that module's existing entry and logical-path checks, without reading files or touching the binary-sync plan. `content_mirror.plan` will validate references on both current projections before classifying an entity. Duplicating the grammar risks drift; importing the binary sync workflow would add unrelated behavior.
2. **Use `data.difficulty.check` for explicit ratings.** Map its validated dimensions, total, and model back to mirror field names. This keeps normalization in the approved Data authority and avoids both a new Domain import and a nested `apply` transaction.
3. **Keep schema handling projection-based.** Derive the stale-clear and SQL update field set from fields actually present in the authored projection. Explicit non-null ratings require the complete group. A schema migration or guessed null columns would make old pools behave differently and is not needed.
4. **Reuse `recover_converged` for remote projection adoption.** The planner will allow that existing classification only when the repository revision is exactly the local revision plus one, the incoming payload contains the current pool projection, and normalized content equals the pool. The existing apply path then records the revision and full baseline once; the next plan is a no-op. A new status or a general relaxation of revision checks would widen the interface.

## Risks / Trade-offs

- [A pool may contain an invalid legacy logical figure reference] → Preflight checks both sides and refuses the entity before mirror writes; byte existence remains the separate figure-sync contract.
- [An older v1 client may not recognize the additive fields] → Keep the documented revisioned projection upgrade and require callers to check before syncing; do not claim cross-version writes are transparent.
- [SQLite schema may contain only some difficulty columns] → Keep projection and SQL writes limited to present fields, while refusing explicit ratings that need the whole group.

## Migration Plan

No SQLite migration or JSON schema-version bump is required. A workspace with an older baseline exports its current projection on the next forward revision; another workspace may adopt that exact next revision when its pool matches. `check` remains the zero-write preview before `sync`. Reverting the code requires no data rollback, though a previous client may reject the newly allowed fields until the projection is brought back to its earlier shape through an explicit forward edit.
