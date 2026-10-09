## Approved contract

Implement `kp-text-typesetting-check` and ADR 0023. The 40–300 body-only band is
inclusive; zero-visible paragraphs do not trigger the lower bound. Findings
never become gate errors, content changes, authoring advice or nonzero exits.

## Modules and flow

`workbench/domain/typesetting.py` owns `check(rows, available=True)` and
`render_text(report)`. Rows provide `kp_id` (or bundle `key`) and `body` only.
Measurement normalizes CRLF in a local copy, splits on blank/whitespace-only
lines, and removes math/backticked constructs for counting. Constructs are
recognized over the whole body so fenced code spanning blank lines is excluded
throughout; original paragraph boundaries and the input text are preserved.
Measurement trims paragraph edges; interior whitespace and line breaks count.
All original nonempty paragraphs, including zero-visible ones, enter totals,
extremes and nearest-rank percentiles; only the short-bound test excludes zero.

`workbench/data/typesetting.py` reads body/id rows from a supplied connection.
It performs no schema ensure, migration or writes. Missing table/body/id returns
unavailable input. Ingest attaches the pure report after successful existing
validation and retains it through apply and both result allowlists. Its pure
`inspect_content_bundle_typesetting(manifest)` helper distinguishes absent input
from a checked empty bundle; it does not replace validation of malformed input.

The pipeline hook explicitly imports helpers from its own repository root so a
standalone script cannot pick up an editable-installed checkout. It obtains the
report before the existing schema gate early return, using a read-only SQLite
connection. Existing findings, ERROR/WARNING counts and exit rules are unchanged;
typesetting has its own advisory JSON key and shared text inside the existing
report, with no second report artifact.

## Report contract

The additive shape is defined in `FILE_CONTRACT.md`. It holds availability, the
band, over-long and short sections, one row per flagged knowledge point with both
bound counts and min/max, and scope totals/nearest-rank percentiles plus each
side's knowledge-point count/share. Both-sided points occur only in over-long.
No-input and checked-clean reports are distinguishable. Empty percentile values
are null and empty-scope shares are zero.

## Scope and acceptance

Use temporary fixture databases for all writes, migration or rollback tests.
Any real course database read uses `mode=ro`. No registry edits, course content
repairs, schema changes or other frozen-layer fixes. Focused TDD covers boundaries,
constructs, report order, unchanged input/rows/batches, non-blocking ingest and
legacy schema-error behavior. Required original sections 1–4 are tracked separately
from deferred sections 5–6; parent owns independent acceptance and archive.
