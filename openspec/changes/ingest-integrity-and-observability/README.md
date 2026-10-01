# ingest-integrity-and-observability

A **defect register**, not a change in behaviour. Two course-ingest jobs
(`ncmc`, `c04`) finished in the last four days and neither could report whether
it had lost anything; in `c04`'s case it had.

| file | what it holds |
|---|---|
| `proposal.md` | Why the register exists, and how each item is routed to a fix |
| `design.md` | The evidence ledger — a `file:line` or a reproducible query behind every row, plus what was refuted and what is still unverified |
| `tasks.md` | The queue. Each task names its route and the capability that owns it |

Start with `tasks.md` §1: those items are bugs against requirements the
repository already carries, so they need no new spec and no doctrine decision.

## The four routes

- `CONFORMANCE` — a requirement exists and the implementation violates it.
- `NEW-GAP` — no requirement exists; a follow-up change must author one.
- `DOCTRINE` — all four sit in `pipeline/`, whose behaviour contract
  `AGENTS.md:38-39` freezes. They need a decision before they can become
  requirements.
- `NOT-A-DEFECT` — looks wrong, is what the spec requires. Recorded so nobody
  "fixes" it.

## The headline

`c04` lost 37 problems to a dedup and rebuilt its manifests, and problem ids are
minted by a positional counter — so a rebuild re-mints them from position rather
than identity. Diffing the live pool against the 974-row pre-deletion snapshot in
`pool/backups/` gives 37 deleted, 0 added, and **425 of the 937 surviving ids now
denoting a different question** (512 unchanged). `c04-ch01-prob-204` was
「新古典增长模型中储蓄率变化的影响。」 and is now 「用数理方法和几何方法推导BP曲线…」.
`problem_attempts` / `problem_progress` / `review_schedule` key on the same strings.

## What this change does not do

No code, no schema, no migration, no data write, no requirement change, no test.
`skip_specs: true` is declared in `.openspec.yaml`, and it is honest here: a
register of defects changes nothing. Where an item does imply a new requirement,
`tasks.md` says so and leaves the requirement to a follow-up change.

Every query in `design.md` is read-only and was run in `mode=ro`. No pool is
touched by this change.

## Audit trail

2026-10-01, against the merged tree (`#80`–`#90` landed): every `repo:` citation
re-read, the headline `c04` diff re-run (the pool kept evolving — see the
design.md audit note), the server-side double-escape no longer reproduces, and
the graph-semantics NOT-A-DEFECT row is half-superseded by `#87`/`#90`. Details
in `design.md` and `tasks.md` §1.2/§3.1/§7.1.
