# PR123 specification repair report

Date: 2026-10-13

Target worktree: `D:\Projects\Academic Workflow\lesson-kit\.worktrees\pr123-audit-20261013`

Base HEAD: `020755e41c196b16ec5c031b6cec821519229da8`

## Result

The PR123 OpenSpec delta now reconciles three current capability requirements:

- `problem-difficulty` / `Rating invalidation on content change`: content-only edits still clear the complete stored rating and do not rerate it. A complete, explicit replacement vector in the same JSON mirror revision is validated and stored with derived total/model values.
- `knowledge-figures` / `Declared figure area`: a JSON mirror may update validated logical references for an already-tracked owner without checking byte existence or changing files. Gated figure assets retain their existing byte-hash verification, and repository-wide naming remains unresolved.
- `knowledge-figures` / `Gated figure patch channel`: new image generation and asset attachment remain behind the manifest and byte-verification gate. Reference-only mirror updates cannot create, copy, rename, transport, or attest figure bytes.

The six prior scenarios in those requirements are preserved exactly after line-ending normalization. The three modified requirements contain 10 scenarios total: the 6 preserved scenarios plus 4 clarifying scenarios. Per requirement:

| Requirement | Prior scenarios preserved | Total scenarios in delta |
|---|---:|---:|
| Rating invalidation on content change | 1 | 2 |
| Declared figure area | 2 | 4 |
| Gated figure patch channel | 3 | 4 |

The proposal, design, tasks, and dated PR123 changelog were updated to match. No source, test, DDL, data, runtime, transport, archived-spec, or live-spec files were changed. No full-suite or isolated acceptance rerun, OpenSpec archive, push, or merge was performed.

## Verification

- `openspec.cmd show expand-content-mirror-fields`, `openspec.cmd show problem-difficulty --type spec`, and `openspec.cmd show knowledge-figures --type spec`: inspected the change and authoritative current requirements.
- `openspec.cmd status --change expand-content-mirror-fields`: all 4 planning artifacts complete.
- `openspec.cmd instructions --change expand-content-mirror-fields specs`: read the spec-delta contract.
- `openspec.cmd instructions --change expand-content-mirror-fields archive`: read archive inputs only; no archive action was run.
- `openspec.cmd validate --all --strict --concurrency 3`: 24 passed, 0 failed.
- `git diff --check HEAD`: passed.
- PowerShell scenario-block comparison between the current live requirements and the three MODIFIED delta requirements: 6/6 prior blocks equal; 4 new scenarios; 10 scenarios total.

The prior independent source and isolated acceptance applies to base HEAD `020755e41c196b16ec5c031b6cec821519229da8`. This docs-only follow-up is limited to the contract boundary above and awaits the separately assigned bounded review.
