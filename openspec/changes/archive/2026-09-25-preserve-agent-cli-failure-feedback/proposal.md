## Why

In the first physics-workspace conversation, the Agent omitted the workspace
argument from `lesson-kit data`. Argparse reported the error and exited 2,
but piping the command to `head` masked that exit status. Pi reported a done
activity, while the error text remained inside collapsed output.

## What Changes

- Teach the correct CLI argument order and subcommand `--help` discovery.
- Instruct the Agent to run Lesson Kit commands independently, without pipelines,
  `|| true`, or later successful commands masking their exit status.
- Show a sanitized, bounded error summary directly on failed activities while
  keeping full tool output collapsed.
- Preserve provider-reported failure status; never infer failure from the word
  `error` in otherwise successful output.
- Allow a corrected invocation to succeed without erasing the earlier failure.

## Capabilities

### Modified Capabilities

- `ai-teacher-bridge`: CLI invocation guidance and truthful tool outcomes.
- `workbench-ui`: visible failed-activity summaries.

## Impact

Agent prompt, normalized activity presentation, and focused regression tests.
Keep argparse, existing business-error output, and the current event transport.
No new CLI error protocol, dependency, or real learning-pool mutation.
