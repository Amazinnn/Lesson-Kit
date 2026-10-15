# Load only for Lesson Kit

Keep this directory in the Lesson Kit repository as the versioned source. For a local deployment, copy `SKILL.md` and `TERMINOLOGY.md` together into:

```text
~/.lessonkit-workbench/skills/source-bounded-learning-drill/
```

In the existing Lesson Kit `~/.lessonkit-workbench/bridges.json`, append these two argv elements to the Pi provider's existing `args`:

```json
["--skill", "<absolute path to the directory above>"]
```

Preserve all other provider settings and args. Named Pi model entries with their own explicit `args` override the provider args, so append the same pair there too when such entries exist. Do not replace models, credentials, budgets, other skills or existing flags. Do not set `PI_CODING_AGENT_DIR` to the skill directory.

The existing Lesson Kit launcher forwards these args to Pi in both print and RPC mode; no product-code change is needed. All registered course workspaces share this one Lesson Kit-owned copy. No course-folder installation and no edits under Pi's global config are required. Starting Pi outside Lesson Kit does not receive these Lesson Kit bridge args.

Use `pi --help` to confirm `--skill` support. For a zero-generation load check, start an isolated offline RPC process with the configured args and request `get_commands`; confirm `skill:source-bounded-learning-drill` points to this deployed directory. This checks loading, not generated-question quality.

A Pi RPC process already running for a conversation keeps its existing resources. Use a new Lesson Kit conversation, or wait for normal idle process recycling; do not interrupt an active turn to force a reload. Existing conversations with explicitly pinned nonempty `model_args` keep those args until their model target is explicitly changed; do not silently rewrite their records. Update the two deployed skill files together when upgrading the repository source.
