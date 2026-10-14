# 2026-10-14 Agent model picker and saved-paper recovery

The new-conversation model picker now uses native vertical scrolling inside the desktop Agent column. The existing narrow drawer scroll path and hidden state remain intact. No JavaScript handler, provider call, API, CLI, or database change was needed.

The reported ADS papers were selection manifests in the conversation job directory, not managed saved papers. The existing running service API saved their ordered existing problem IDs as ps-003 and ps-004 (12 each). Independent read-only API and page checks confirmed both records. The original job manifests and old saved papers were preserved; course SQLite bytes were unchanged. This recovery adds no automatic Agent-save behavior.

Independent acceptance at 565bd4bc: 988 Python tests, 164 Node tests, compilation, strict OpenSpec validation, extract-problems guard, and native Edge desktop/drawer scrolling passed. No paid LLM test or human visual acceptance is claimed. The optional problem-set guard was not applicable because its output was absent.

The stylesheet alone was deployed to the existing port-3081 runtime without restarting it. OpenSpec fix-agent-model-picker-scroll was archived with the CLI; its behavior is now in the current workbench-ui specification. Concurrent main changes from PR #124 were integrated without altering their CLI implementation. Final integration and release evidence is recorded separately by the independent acceptance runner and PR CI.
