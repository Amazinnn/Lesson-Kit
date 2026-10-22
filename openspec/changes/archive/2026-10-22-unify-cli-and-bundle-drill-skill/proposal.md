# Unify CLI discovery and bundle the drill skill

## Why

The installed CLI dispatches 27 commands, but its root help hides four commands
and `python -m workbench.cli.main` rejects them. `ingest bundle` is similarly
callable but undiscoverable. The material-bounded drill skill currently requires
a manually copied directory and per-provider arguments despite being owned by
Lesson Kit.

## What Changes

- Use one real argparse command tree for installed and module entry points,
  including extension commands and `ingest bundle`.
- Preserve existing arguments, validation, output payloads and exit codes.
- Ship the existing drill skill and its terminology unchanged as a Bundled
  Lesson Kit Skill; automatically load it for Pi launched by Lesson Kit.
- Preserve other provider arguments, native configuration and sessions. Replace
  only known legacy Lesson Kit skill arguments at launch, without rewriting
  configuration or conversation history.

## Impact

- Affected specs: review-workbench, ai-teacher-bridge.
- Affected code: CLI shell, Pi command construction, package resources.
- No database/schema/course migration, new command, teaching redesign, Pi global
  configuration change or new dependency.
