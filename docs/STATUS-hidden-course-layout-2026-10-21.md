# Hidden course artifact layout - 2026-10-21

Implemented the approved scope from 806e8cd2. New courses use `.lessonkit/pool/`; legacy pools remain usable until explicit migration. All new internal/default work stays under `.lessonkit/`; explicit exports remain supported. External tool output directories, source materials, old exports and nested workspace copies are out of scope.

Code: 99424bc6; corrected fresh-init assertions a8721f7e; balanced Markdown links8215c0ae; legacy consumers b03bdf9a. Frozen pipeline source, schema and learning-data semantics are unchanged. Contracts, installed Agent guidance and canonical pool-pipeline instructions are coordinated. DATA_MODEL has no affected field semantics.

Verification: final code b03bdf9a passed1148 tests in215.09s; final integration covering107 passed14.02s; layout31 cases passed within that covering run. Compileall, strictall26/specs19 and extractionguard passed before archive; after archive strictall25/specs19 passed. No generated output exists for the conditional problem-set guard.

Review: task implementation and parenthesized-link repair approved. The whole-branch reviewer read all3272 lines but reached its usage limit after identifying the legacy guard/image boundary. Its findings were preserved and closed by the independent629-line integration repair review, which also read18 new scenario lines. No unresolved Critical/Important finding remains; controller performed overall acceptance.

Isolated ADS acceptance copied the three owned/internal areas into a separate registry/workspace. Only copied fixture provenance prefixes were normalized before the preservation baseline; the real source was untouched. All308 moved files and DB bytes/schema/29 tables/2494 rows were preserved,108 batches readable, preview zero-write and repeat no-op verified. CLI internal writes/explicit external output and HTTP practice/hub checks passed; no real provider was used.

Real rollout: main fast-forwarded to99765c0f after prior remote main CI success. Only ADS root pool144 files and intermediate164 files were moved into `.lessonkit/`; all308 files remained byte-identical, with zero Markdown edits. The DB bytes and all29 tables/2494 rows matched the external before-copy. Existing hidden files, other registry entries and the user's PENDING-DEFINITIONS edit were preserved; unrelated course paths and Project2 processes were retained. No course-data migration or cleanup occurred.

Managed3081 restarted from main (PID26168). Actual ADS practice page200; hub86 KPs/534 problems/87 due. Changed static bytes match main. The shared installed pool-pipeline instruction section was updated with a before-copy, preserving its frontmatter/custom workflow. New background launch uses OS-supported breakaway from the execution helper's Windows job without changing product service code.

Archive:2026-10-21-hidden-course-artifact-layout. All old review-workbench requirement/scenario headings retained. Runtime and migration receipts/backups: `~/.lessonkit-workbench/deployments/20261021-hidden-course-layout/`. Final push/CI outcome is recorded in runtime-receipt.json and STATUS.md there; this repository record is the pre-push snapshot.

Migration reverses caught operational failures; it is not a cross-process-crash filesystem/registry transaction. The accepted real rollout used an idle-turn/provider audit and an external before-copy. No deferred feature or unrelated cleanup is included.
