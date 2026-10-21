# Why

Lesson Kit currently mixes its private database/build files with a learner's course materials. The approved goal is to keep new internal outputs under `.lessonkit/`, preserve existing workspaces, and move only clearly owned directories on explicit request. This implements the workspace layout terminology in GLOSSARY; it does not clean up course materials or external tools.

# What Changes

- New workspace initialization uses `.lessonkit/pool/<course>.db` and internal build/output paths under `.lessonkit/`.
- Legacy workspaces retain their existing layout until explicitly migrated.
- A human CLI previews and explicitly migrates root `pool/` and `intermediate/`, preserving history and updating registration/path consumers.
- Explicit user export destinations remain supported; Agent/default internal work stays hidden.
- Verify on an isolated copy before applying to the authorized ADS workspace.

# Impact

Affected: workspace discovery/init, filesystem/path consumers, Agent output instructions, artifact contracts and human CLI inventory. No new schema, dependency or learning-state semantics. Frozen pipeline interfaces keep their contracts. External harness output, nested workspace copies, course materials and existing exports are excluded.
