# Design

Use the existing registered database path to distinguish hidden and legacy workspaces; do not add a second registry or automatic migration. Centralize only the path decisions needed by current consumers. New init creates the database under `.lessonkit/pool/`; legacy discovery continues to recognize `pool/`. Ambiguous live pools are refused.

The explicit `lesson-kit workspace <name> migrate-layout [--apply]` operation previews by default. Applying moves only owned root `pool/` and `intermediate/` directories into `.lessonkit/`, preserves bytes/history and redirects registry and known path consumers. Persisted historical references must remain resolvable; prefer narrowly scoped resolution over bulk rewriting arbitrary source strings. Preflight source/destination containment and collisions before mutation; failure must not leave a registration pointing to a missing database. Repeat application is a no-op on a completed layout. No symlink/junction compatibility aliases at the course root.

Only explicitly requested exports leave the hidden area. Workbench staging, default outputs and maintained Agent instructions use `.lessonkit/`. Existing pipeline APIs remain usable through their explicit arguments/adapters; do not modify frozen behavior contracts.

Migration acceptance uses an isolated ADS copy with its own registry, then the real authorized ADS course during a managed-service stop window. Compare moved file bytes and database schemas/rows before/after; verify existing images, saved papers, history and ongoing read/write destinations. Course materials, old exports, external tool directories and the nested `课程文件结构/` copy are unchanged. No history pruning or content repair belongs to this change.
