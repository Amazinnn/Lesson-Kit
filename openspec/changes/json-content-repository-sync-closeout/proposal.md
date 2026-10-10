# Proposal: JSON content repository sync closeout

## Why

PR110 implements the Git-backed JSON authored-content mirror under change
`json-content-repository-sync`. Independent review established two P2 defects:
R1 (an interrupted missing-file restoration cannot be retried), repaired at
`b66eb03` and awaiting re-review, and R2 (bootstrap silently discards
unreadable repository JSON, reports a valid result, and creates a canonical
file next to an unreadable renamed copy), which is still unfixed. The
independent engineering acceptance at `64daa44` is explicitly incomplete:
documentation drafts are uncommitted, the contract-authority files lack the
mirror tables, task checkboxes are not mapped to evidence, two full-suite
failures are undiagnosed, and the isolated real-pool acceptance did not finish.
The owner authorized merging PR110 only after repair, documentation, and final
gates are complete; this change is the auditable plan that closes those gaps.

## What Changes

- Repair bootstrap input verification (R2): every existing file in the scanned
  course subtree is accounted for; unreadable files (invalid UTF-8, malformed
  JSON) appear in the machine-readable bootstrap report; canonical creation is
  refused for any entity whose identity an unreadable file makes ambiguous;
  independently identifiable siblings still bootstrap. Behavior change captured
  in the delta spec below.
- Assess the per-entity write-failure escape in the bootstrap loop (an
  `_atomic_write`/`_put_state` exception exits the loop and later siblings are
  never attempted). It contradicts the already-specified resumable,
  per-entity bootstrap, so the minimal repair lands in this change unless the
  assessment shows it widens v1 scope, in which case it is deferred as an
  explicit follow-up task. No new requirement is added for it.
- Finish the contract-authority documentation inside the same PR:
  `docs/DATA_MODEL.md` gains the `content_mirror_state` / `content_mirror_log`
  field, writer/consumer, and state-lifecycle contract; `docs/ACTION-GRAPH.md`
  registers the mirror actions; changelog and indexes are updated;
  `docs/PRODUCT-MANUAL.md` gains the mirror chapter; the already-drafted
  `FILE_CONTRACT.md`, `docs/ARCHITECTURE.md`, and `docs/GLOSSARY.md` updates are
  completed and committed; the sibling change's stale `design.md` sentence that
  says bootstrap refuses when mirror state already exists is corrected to the
  implemented resumable skip-and-continue behavior.
- Map the sibling change's `tasks.md` checkboxes strictly to existing evidence
  (acceptance reports, focused suites, real-copy results); no checkbox is set
  from intent, and the external rollout tasks stay open.
- Diagnose the two full-suite failures
  (`ConversationTests.test_a_quiet_command_gets_the_tool_budget`,
  `ConversationTests.test_output_past_the_budget_is_not_a_timeout`) against
  `origin/main` on this machine and record the evidence. A fix belongs to a
  separate main-side change; once shown to be environment-owned they do not
  block PR110 and are documented as a follow-up.
- Re-run the isolated real-pool acceptance on the final HEAD: rerun the c02
  ledger-failure case with the pre-call DB snapshot and requested JSON bytes
  persisted separately and asserted independently; complete the c04 E2E after
  its recorded legacy baseline upgrade; confirm zero writes to the 17
  registered learner databases and to the external `Lesson-Kit-Content`
  snapshot.
- Run the full repository gates on the final HEAD: `pytest tests -q`, the Node
  suite, `compileall`, `openspec validate --all --strict`, and the
  extract-problems guard (problem-set guard only if its output exists).
- Merge mechanics: refresh the remote PR head, push the local HEAD to
  `feat/canonical-content-sync` as a fast-forward, update the PR110 body to the
  final scope and evidence, wait for the 3.11/3.12 checks, merge with
  `--match-head-commit`, verify CI on the actual merge commit, and only then
  repoint the installed editable CLI to the accepted worktree.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workbench-content-governance`: bootstrap SHALL verify that repository inputs
  are readable and identity-attributable, SHALL report unreadable files, and
  SHALL refuse canonical creation for entities whose identity an unreadable
  file makes ambiguous, while per-entity partial success is preserved.

## Impact

- `workbench/data/content_mirror.py` bootstrap scan/report path;
  `tests/workbench/test_content_mirror.py` focused regressions for unreadable
  inputs and per-entity write isolation.
- Contract-authority documents in the same PR: `docs/DATA_MODEL.md`,
  `docs/ACTION-GRAPH.md`, changelog and indexes, `docs/PRODUCT-MANUAL.md`,
  `FILE_CONTRACT.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md`, plus the
  sibling change's `design.md` and `tasks.md`.
- PR #110 (branch `feat/canonical-content-sync`): final branch content, CI
  outcome, and merge commit; the installed editable CLI is repointed only after
  acceptance passes.
- Not impacted: pool schema (no new migration), the 17 registered learner
  databases (read-only, isolated copies only), the external
  `Lesson-Kit-Content` rollout (stays open in the sibling change), and the
  conversation-bridge source (diagnosis and a follow-up change only).
