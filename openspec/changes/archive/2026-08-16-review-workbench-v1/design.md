## Context

The confirmed contract for the workbench lives in `docs/ARCHITECTURE.md` (layered
module map), the change specs (26 requirements), and ADR 0009–0021. See
proposal.md for motivation; this design covers the backend only — the frontend
pages are the shell's flexible upper layer.

Constraints that shape the design: stdlib-only Python, single process single
port, no hashes, no defensive programming, additive pool schema only, and the
one-way dependency rule (Shell → Domain → Data; Bridge attached).

## Goals / Non-Goals

Goals:

- A `workbench/` tree with strict module boundaries: `registry`, `domain`
  (weak/pull/feedback/schedule), `data` (pool/migrations/queries), `bridge`
  (jobs/providers/contracts/teacher), `cli`, `server` (app/api/pages).
- Pure-rule domain modules with no IO, unit-testable against an in-memory or
  temp-file SQLite pool.
- The `wb` CLI and the HTTP API share the same domain/data/bridge code — the
  shell is thin in both directions.
- Bridge task lifecycle with output-contract validation for `explain` and
  `diagnose`; no AI kernel; task files under `.lessonkit/jobs/`, validated
  results under `.lessonkit/explain/`.
- Additive migrations via the existing `ensure_*` pattern in `pool_schema.py`.

Non-Goals (backend v1):

- No frontend SPA; pages.py is minimal server-rendered HTML (KaTeX assets
  reused statically from `frontend/editable-graph/dist`).
- No `generate` bridge operation, no Scoropic mode, no teacher-memory consumer.
- No changes to `pipeline/`, `pool/scripts/` behavior, or `lessonkit.py`.

## Decisions

1. **Pool injection into domain**: domain functions take a `Pool` object
   (from `workbench/data/pool.py`) — no connection management in domain code.
   This keeps domain pure and testable with a temp DB.
2. **Registry at user level**: `~/.lessonkit-workbench/workspaces.json` and
   `bridges.yaml`, following the confirmed "workspace registry is global" call.
3. **Schedule key**: `review_schedule` PK `(item_type, item_id, direction)`;
   direction empty for undirected items, per-direction entries for memory-recall
   cards. SM-2 variant as a pure function `after_result(state, result, now)`.
4. **Contract validation is pure text rules**: `contracts.validate(kind, text)`
   returns (ok, reasons) by checking required sections, parseable Markdown, and
   anchor references — no model involvement, fully unit-testable.
5. **Server routing**: `BaseHTTPRequestHandler` with a handler registry
   `{method, pattern, handler}`; JSON API in `server/api.py`, HTML in
   `server/pages.py`; figure serving with resolved-path containment check.
6. **CLI is data-only** (ADR 0020): `wb` commands map 1:1 to data/domain/bridge
   calls; zero teaching semantics, zero prompt text.

## Risks / Trade-offs

- [Server-rendered HTML limits interaction polish] → API stays the contract;
  pages.py can evolve without touching handlers or domain.
- [External CLI flakiness (timeouts, non-zero exits)] → job state machine
  captures failure reasons; UI polls status; validation gates trust.
- [SQLite concurrency (web shell + CLI on same pool)] → single-process server
  with short transactions; SQLite handles concurrent readers; writers are
  brief and serialized.
- [Keyword feedback mapping misclassifies] → note text preserved verbatim;
  mapping rules are unit-tested and trivially editable (ADR 0011).

## Migration Plan

- Deploy: extend `pool_schema.py` with `ensure_workbench_schema` (two new
  tables, three new columns) and call it from `migrate-progress.py`
  (idempotent, additive). Existing data untouched.
- Rollback: remove `ensure_workbench_schema` call; the new tables/columns are
  harmless orphans; no data loss path exists.

## Open Questions

None that change the specs or approach. Implementation details (exact HTTP
route shapes, CLI flag names) follow the spec scenarios and are documented in
`docs/ARCHITECTURE.md`.
