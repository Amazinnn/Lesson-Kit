# Design: JSON content repository sync closeout

## Context

See proposal.md for motivation. Current technical state, verified against the
worktree at `b66eb03` and the durable evidence under
`.superpowers/sdd/`:

- PR110 (change `json-content-repository-sync`, branch
  `feat/canonical-content-sync`) implements the JSON authored-content mirror.
  The branch diff against main `2404f8f` is 18 files, +1935/-4: additive
  `content_mirror_state` / `content_mirror_log` tables, the mirror engine, and
  the CLI group. It touches no `workbench/bridge/` source.
- R1 (interrupted missing-file restoration cannot be retried) is repaired at
  `b66eb03` by writing mirror state before the restored file; the repair is not
  yet independently re-reviewed.
- R2 (bootstrap discards unreadable repository JSON and reports success) is
  unfixed; the defect is mechanically reproduced in the review report.
- Four contract-document drafts are dirty in the worktree and must not be
  discarded; `docs/DATA_MODEL.md` has no mirror field contract yet.
- Acceptance at `64daa44` is explicitly incomplete: two full-suite failures
  undiagnosed, the c02 ledger-failure assertion stopped on a combined check,
  c04 E2E unfinished, and the sibling change's `tasks.md` is not
  evidence-mapped.
- Hard constraints: no hashes, stdlib-only, additive schema changes through
  existing `ensure_*` patterns, new logic in `workbench/`, real learner
  databases read-only (isolated SQLite copies for checks), no external
  `Lesson-Kit-Content` bootstrap or real-course sync.

## Goals / Non-Goals

**Goals:**

- A merge-ready PR110: R2 repaired with focused regressions, R1 re-reviewed,
  per-entity write isolation assessed and minimally repaired if confirmed.
- Complete contract-authority documentation inside the same PR, including the
  `DATA_MODEL.md` mirror-state/ledger contract and the stale `design.md`
  sentence corrected.
- Final full-suite gates and isolated real-pool acceptance run on the final
  HEAD, with the two conversation-suite failures resolved by evidence, not by
  assumption.
- A clean merge: refreshed head, updated PR body, CI verified on the actual
  merge commit, installed CLI repointed only after acceptance.

**Non-Goals:**

- Fixing the conversation bridge timing tests in this PR (they belong to main).
- External `Lesson-Kit-Content` rollout, real-course bootstrap/sync, or any
  learner-database write.
- Archiving the sibling change while its rollout tasks remain open.
- Re-introducing or re-removing `problems.topic_label` (settled by PR112).

## Decisions

### D1 — R2 repair: per-entity identity implication by id occurrence

An unreadable file cannot be parsed, so identity attribution uses the only
available signal: the presence of a pool entity id in the file name or in the
file's bytes decoded with replacement. Implicated entities are refused with the
implicating file named; unimplicated entities bootstrap normally.

Alternatives rejected: (a) refuse the whole course on any unreadable file —
violates the already-specified per-entity partial success; (b) silently skip
unreadable files — the defect itself; (c) best-effort id extraction from
undecodable bytes beyond substring occurrence — speculative parsing of corrupt
data, adds machinery for no reliable gain. An unattributable unreadable file is
reported but not blocking: if it is later repaired into a duplicate identity,
the existing sync duplicate-identity refusal catches it before any write.

### D2 — Per-entity write-failure isolation: treat as confirmed, repair minimally

The reviewer observed that an exception from the per-entity atomic write or
state write exits the bootstrap loop, so later siblings are never attempted —
which contradicts the resumable, per-entity bootstrap contract that the sibling
change already specifies. The repair captures the exception as that entity's
failed result and continues with the remaining entities. No new spec text is
added: the requirement already exists in the sibling delta, and this change
relies on it. If the assessment during implementation shows the repair widens
v1 scope, the task records the finding and defers instead.

### D3 — Conversation-suite failures: diagnose against `origin/main`, do not fix here

The two failures are timing-sensitive tests with a 0.3s idle budget that reset
on subprocess output; the branch diff does not touch `workbench/bridge/`, and
CI (Linux) is green. The diagnosis runs the two tests against `origin/main` in
a throwaway worktree on this Windows machine and keeps the JSON output as
evidence. If they fail on main too, they are environment-owned and are
documented as a follow-up change; PR110 is not blocked. If they pass on main,
the failure is treated as a possible branch interaction and escalated before
any merge step. Fixing the budget here was rejected: it would mix a main-owned
behavior change into the mirror PR.

### D4 — Ledger-failure rerun: persist evidence, split assertions

The previous extended c02 run stopped on a single conjunction that compared a
full pre-call DB snapshot and raw JSON bytes; the scratch writer used
platform-default newlines while the mirror writer uses LF, so the file-bytes
term was a plausible harness artifact that could not be attributed after the
fact. The rerun persists the pre-call full DB snapshot and the requested JSON
bytes to disk before the operation, and asserts DB atomicity and file
normalization as two separate checks.

### D5 — Evidence-mapped task checkboxes

The sibling change's `tasks.md` checkboxes are set only where a named evidence
artifact exists (focused suites, acceptance reports, real-copy results). Tasks
7.1–7.3 (external rollout) stay unchecked; the change stays active.

### D6 — Change/archive boundaries

This change's delta uses `## ADDED Requirements` with a distinct requirement
name, so it never conflicts textually with the sibling's unarchived delta. The
closeout change may be archived once its own tasks complete; the sibling change
remains active until its rollout is delivered and archived separately (or split
into a successor change). No change is archived by this plan while scoped work
is outstanding.

### D7 — Installed CLI repoint only after acceptance

The installed editable CLI currently points at the previous corrected worktree.
It is repointed to the accepted worktree only after the final gates and
acceptance pass on the final HEAD, verified from a neutral working directory.

## Risks / Trade-offs

- [An unreadable file is a corrupted copy whose bytes lost the entity id]
  → reported without blocking; a later repaired duplicate is caught by the
  existing duplicate-identity refusal in sync. Residual risk accepted for v1.
- [The conversation tests still fail after the main-side run] → escalate as a
  possible branch interaction before merging; never rerun until green without
  a cause.
- [Other Windows timing flakes surface in the final full suite] → rerun each
  failure in isolation first and attribute per test with evidence; no blanket
  "flaky" label.
- [Accidental write to a real learner database] → all checks run on isolated
  copies under `.superpowers/sdd/`; live databases are opened read-only and
  verified by metadata readback.
- [c04 legacy ensure backfill side effects] → the recorded post-upgrade
  baseline (`content_sequences` growth, missing runtime tables) is the only
  comparison target for the E2E rerun.
- [Remote PR head moves or CI reruns during the merge sequence] → refresh the
  remote head immediately before push; merge with `--match-head-commit`; verify
  CI on the actual merge commit.

## Migration Plan

Nothing deploys new schema; rollback is simply not merging. The only
user-visible step is repointing the installed editable CLI, which is
reversible. Sequence: repair and focused regressions → documentation and
sibling artifact corrections with explicit-path commits → conversation-test
diagnosis evidence → fresh independent review of the repaired HEAD → final
isolated real-pool acceptance and full repository gates → push, PR body, CI,
merge, merged-CI verification → CLI repoint → handoff document update.

## Open Questions

- When the sibling change's rollout completes, whether the per-entity
  write-isolation behavior should gain its own scenario in the main spec at
  archive time — decidable then without changing this change's tasks.
- Ownership of the sibling change's rollout tasks 7.1–7.3 (external
  `Lesson-Kit-Content` bootstrap and samples) — a future change, explicitly
  out of scope here.
