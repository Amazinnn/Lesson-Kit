# CLI discovery and bundled drill skill — 2026-10-22

Approved scope: expose the existing CLI consistently and ship the existing
material-bounded drill skill with Lesson Kit. No new command, teaching redesign,
schema change, course migration, new dependency or Pi global installation.

Implementation: `e13a9080`, precise test naming `56a2992a`, semantic-error usage
fix `fc5bb8a7`. The parser owns all 27 existing commands and `ingest bundle`;
console, `workbench.cli.main` and `workbench.cli.entry` share dispatch. Existing
extension namespace handlers retain their business behavior. Pi print/RPC
commands load the packaged skill after provider/model arguments are selected;
only known managed legacy/bundled skill arguments are normalized at launch.
Configuration and pinned conversation records are not rewritten.

Teaching resources match the original base `944b867c` Git blobs exactly:
SKILL.md 11013 bytes, TERMINOLOGY.md 13342 bytes. Narrow `.gitattributes` entries
preserve their LF bytes across Windows checkouts. Existing `.claude` entries
are thin references; package data includes both canonical files.

Verification: full suite at `56a2992a` passed 1154 tests in 259.40s. The subsequent
usage-only fix passed 13 targeted tests, including its new red/green regression.
Compileall, strict current specs 19/19, strict all 26/26 and dmath/ch06 extraction
guard passed. No generated output exists for the conditional problem-set guard.
Independent task review approved spec compliance and quality through `fc5bb8a7`.

A wheel installed in a separate virtual environment passed 87 actual help
checks across all three entry forms, exact resource-byte comparison, and a
managed-paper round trip: console save receipt, both module list/get read-back,
and HTTP page read-back. The isolated fixture DB remained byte-identical.
The final wheel was rebuilt after `fc5bb8a7`; both module forms confirmed the
correct semantic-error grammar and exit 2.

Real Pi RPC `get_commands` returned exactly one drill skill with sourceInfo.path
inside the wheel installation. The legacy managed argument was replaced and
bridges.json remained byte-identical. No prompt was sent and session persistence
was disabled; this proves discovery, not generated-question quality.

Release uses `.worktrees/runtime-main` to avoid switching or modifying the
separate visual-design checkout. Operational receipts, final runtime and remote
CI evidence are kept outside course folders at
`~/.lessonkit-workbench/deployments/20261022-cli-bundled-skill/`.
