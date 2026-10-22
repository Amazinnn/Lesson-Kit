# CLI discovery and bundled drill skill implementation plan

**Goal:** repair discovery and entry parity for existing CLI operations, and
load the existing drill skill automatically for Lesson Kit Pi launches.

**Architecture:** Shell → Domain → Data remains unchanged. Reuse actual argparse
parsers and existing namespace handlers. Bundle Markdown with setuptools package
data and inject a resource path at the shared Pi command builder. No new
dependency, registry, CLI command, schema or teaching content.

1. Controller records OpenSpec delta and reconciles scoped documentation.
2. Implementation worker owns CLI/Bridge/package resources and focused tests;
   demonstrate red tests, then implement one shared command tree and resource
   loading. Commit the coherent implementation.
3. Controller verifies command help and isolated papers save/list/get, installs
   a wheel in a temporary environment, and checks real Pi RPC discovery without
   a generation prompt.
4. Independent review covers contracts, compatibility and package/runtime paths.
   Resolve findings, then run pytest, compileall, strict OpenSpec and the extract
   guard. Do not require missing generated problem-set artifacts.
5. Archive the completed delta, integrate main after checking current CI, deploy
   installed CLI/service from a clean main checkout and verify process/import
   location and served behavior. Preserve the unrelated visual-design branch.

All real course data and Pi global configuration are outside this task's write
boundary. Existing active provider work must remain uninterrupted.
