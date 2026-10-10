## Why

The approved `kp-text-typesetting-check` requirement and ADR 0023 define a
read-only body measurement but have no implementation. This follow-up implements
that approved requirement without adding another normative delta.

## What Changes

- Add a shared pure body measurement and factual text report in `workbench/domain`.
- Add the report to valid bundle checks and successful applies, including existing
  CLI and Bridge results; expose a pure pre-apply inspection helper.
- Read chapter-scoped bodies through `workbench/data` and attach the same report
  to the existing pipeline validator output, including legacy schema failures.
- Keep findings advisory, stored text unchanged, and all existing refusal rules,
  accounting, batch semantics and exit codes intact.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None beyond the approved ADDED requirement in
`../kp-text-typesetting-check/specs/workbench-content-governance/spec.md`.
`skip_specs: true` avoids duplicating that requirement. The original change owns
the normative addition; this change owns its implementation and evidence.

## Impact

The only frozen-layer exception is the pipeline validator's read-only
typesetting hook/output. No schema change, new CLI option, dependency, hash or
content rewrite is included. NEW-GAP, DOCTRINE, #110 and original tasks 5–6
remain outside scope. Independent full-suite and isolated acceptance precede
archive; this implementation does not archive or push.
