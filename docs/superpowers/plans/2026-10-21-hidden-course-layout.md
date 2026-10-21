# Hidden Course Layout Implementation Plan

> For agentic workers: use subagent-driven-development, with controller-owned contracts and deployment.

**Goal:** Put new Lesson Kit internal artifacts under `.lessonkit/`, retain legacy workspace compatibility, and explicitly migrate the ADS workspace without losing history.

**Architecture:** Reuse the registered pool path and stdlib path operations. Shell remains thin; filesystem layout/migration is separate from learning rules; SQLite access remains in Data. Frozen pipeline contracts are unchanged and invoked with existing explicit arguments where needed.

**Tech Stack:** Python stdlib, existing argparse, pytest and OpenSpec. No dependency or schema addition.

## Global constraints

- Approved scope: docs/design/2026-10-21-course-artifact-layout-alignment.md.
- New databases: `.lessonkit/pool/<course>.db`; internal build work: `.lessonkit/intermediate/`; existing hidden areas keep their paths.
- Unmigrated legacy workspaces keep working; no automatic move during init/open/read.
- `lesson-kit workspace <name> migrate-layout` previews; `--apply` explicitly applies. Move only root `pool/` and `intermediate/`, preserving backups and history. Never merge colliding destination directories or choose silently between two pools.
- User-requested output paths remain valid. Default/internal outputs and Agent work files stay hidden. External harness directories, source materials, nested copies and existing readable exports are out of scope.
- Do not modify pipeline/, pool/scripts/, lessonkit.py behavior, pool schema/content/learning semantics, or real course files during implementation.
- Migration runs only while the workspace has no active provider/turn and the service cannot access the database. Verify an isolated copy before the authorized ADS move.
- Preserve main's user-owned docs/PENDING-DEFINITIONS.md and untracked files.

## Task 1: Layout, command and regression checks (worker)

Owned files: workbench/** and tests/**. Controller owns docs/specs/skills.

- [ ] Inventory path consumers, especially inferred roots, ingest references and generated outputs; agree minimal approach before edits.
- [ ] Write and run failing tests: fresh hidden init/discovery; legacy compatibility; dual-layout refusal; migration preview/apply/repeat/collision; all moved file bytes retained; known references resolve afterwards; output defaults and explicit exports.
- [ ] Implement a small shared layout resolver and explicit migration using existing registry, path arguments and filesystem tools. No generic persistence subsystem.
- [ ] Thin CLI command and machine surface declaration; update affected consumers instead of rewriting frozen contracts.
- [ ] Run focused/covering tests with PYTHONUTF8=1; commit owned files and report evidence/limits.

## Task 2: Contracts, acceptance and rollout (controller)

Owned files: glossary, FILE_CONTRACT, architecture, manual, action graph, runtime Agent contract coordination and pool-pipeline documentation; change specs/tasks; delivery status.

- [ ] Record requirements before implementation; reconcile affected authorities only. No DATA_MODEL change unless implementation must change persistent field semantics.
- [ ] Review complete implementation and contracts independently; repair any correctness findings.
- [ ] Run full pytest tests, compileall, strict all/spec OpenSpec, dmath/ch06 extraction guard; conditional problem-set guard only with generated output.
- [ ] Copy ADS internal directories to an isolated workspace/registry; preview/apply and verify byte-level preservation, database schema/rows and references; prove no source/nested/export changes.
- [ ] Archive only this change once accepted; preserve existing current-spec scenarios and validate again.
- [ ] Audit service/turns, integrate accepted branch preserving user work, stop managed service, perform explicit ADS migration with before/after evidence, restart and verify actual HTTP plus db registration/path.
- [ ] Push and verify final main CI; record durable runtime/migration receipt and leave feature worktree clean.
