## Why

The pool already stores durable problems with provenance, and `pull` already
selects them, but the CLI is not a usable data interface for composing a
practice set. `lesson-kit pull` returns identifier strings only (the HTTP API
returns whole rows), it cannot express the scoped `include_ids` filter its own
spec requires, it cannot select by exam year, and nothing in the CLI can turn a
selection into the two printable artifacts the problem-set view promises — those
are written by hand today. Meanwhile the declared interface map has silently
drifted (`/pull-cards` is marked as reachable from both surfaces but has no CLI
command; the registration document counts 31 routes and 20 commands where the
code has 32 and 22), and several commands are weaker than their own API
counterparts.

## What Changes

- Extend `lesson-kit pull` into the single composition entry point: scope
  (chapter lens or knowledge points), explicit problem ids, conditional filters
  (source kind, origin kind, difficulty range, and the new `exam_year`), and
  learner-driven selection (weak, due, wrong). Every selected problem reports why
  it was selected.
- Print full problem rows by default (aligning the CLI with `/pull`), keep the
  identifier-only shape behind `--ids`, and add the missing `--include` filter.
- Add `pull <workspace> check --input <file|->` (zero writes) and
  `pull <workspace> --plan <file> --print <dir> [--name <base>]`, which render a
  student practice set and its aligned solution file from the pool, with no
  answers or internal identifiers in the student file and `待补` for missing
  solutions.
- Add an optional `exam_year` problem field (additive, nullable, no backfill)
  with a prefix filter, plus its write paths.
- Make the declared surface a machine-checked fact: one ownership table for
  every API route and CLI command, enforced by a test against the real parser and
  route table.
- Close four CLI gaps found by the audit: `practice` validates the problem and
  writes in one transaction, `feedback` accepts cards and directions, `goals`
  invalidates the cached plan, and the read commands (`weak`, `due`, `ls`)
  gain a JSON form. Remove two dead surfaces (`ingest render --target`,
  `ingest gate|apply` entity values that are always rejected).

## Capabilities

### New Capabilities

- `practice-set-export`: composing one practice set (selection modes, per-problem
  reason, manifest, zero-write check, rendered student set and solutions).

### Modified Capabilities

- `review-workbench`: the pull engine gains explicit ids, exam-year filtering,
  learner-driven selection and per-problem reasons; the CLI entry point records
  the machine-checked surface and the JSON form of the human read commands.
- `workbench-content-governance`: problems gain an optional `exam_year`
  provenance datum with a validation contract.

## Impact

Additive pool column, additive pull parameters, one new CLI sibling action, two
new workbench modules and one ownership table; current learning tables, the
existing practice page, the API response shapes, and every stored row are
untouched. No new dependency.
