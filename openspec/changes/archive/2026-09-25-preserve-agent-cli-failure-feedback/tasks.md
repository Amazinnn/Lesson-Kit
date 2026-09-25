# Tasks

- [x] 1. Verify the current prompt, CLI parser, provider normalization, and activity renderer before editing.
- [x] 2. Add regression coverage for missing workspace/unknown argument exit codes and accurate prompt examples.
- [x] 3. Add prompt guidance to consult subcommand help and preserve CLI exit status through independent invocations.
- [x] 4. Add failed-activity summaries with redaction, 240-character bound, empty-output fallback, and collapsed full output.
- [x] 5. Test Pi isError=true, successful output containing error, and separate failed/corrected invocation rows.
- [x] 6. Run affected tests and OpenSpec strict; perform isolated acceptance and update evidence/hand-off records.

## What changed

- `workbench/bridge/conversations._prompt`: the Agent now gets the workspace-aware
  argument order (`lesson-kit <命令> <工作区名> …`, with an example built from the
  active workspace), the rule to query `--help` instead of guessing flags, the rule
  to issue Lesson Kit commands on their own (no `| head`, no `|| true`, no `&&`/`;`
  chaining; redirect to a file, then `echo $?` when the exit status matters), and
  the rule to claim success only from a successful result.
- `workbench/bridge/conversation_providers._pi_failure_summary`: a failed Pi
  activity carries a `summary` — the last meaningful line of its **already
  sanitized** output (redaction precedes truncation), bounded to 240 characters,
  with an explicit generic message when there is none. Status still comes only
  from the provider's `isError`; nothing scans text to decide failure.
- `workbench/server/static/workbench.js` renders that summary outside the
  disclosure (`ai-plan-summary`), so the reason is readable without expanding;
  the full bounded output stays folded.

## Evidence (2026-09-23)

Repository checks on the working tree: pytest **549**, Node **114**,
`compileall` exit 0, `openspec validate --specs --strict` **11 passed**, `doctor`
all checks passed, both guards PASS.

Regression tests added:

- `test_cli.py`: missing workspace argument and unknown argument both exit 2 with
  a diagnostic; the business-error path still prints JSON and exits 2.
- `test_conversation_providers.py`: failed activity carries a bounded, redacted
  summary; a long error line keeps its diagnostic lead-in; empty output yields the
  generic message; a successful call whose output mentions error keeps `done` and
  gets no summary; a corrected call keeps its own id and outcome.
- `test_conversations.py`: the prompt states the workspace-aware example, `--help`
  discovery, independent execution, and the no-false-success rule.
- `workbench_ui_interactions.test.js`: a failed row shows its summary without
  expanding while the output stays folded; a corrected retry keeps the earlier
  failed row and shows no summary on the successful one.

Isolated real-Pi acceptance (`%TEMP%/lk-cli-fix`, scratch workspace, no real pool
touched; evidence `acceptance.json` + `lk-cli-failure-summary.jpeg`): asked for a
CLI-backed fact, Pi first ran `lesson-kit --help` and `lesson-kit data --help`,
then `lesson-kit data dmath list kp` with the workspace in the right place and
answered "31 个知识点" from `exit=0` output. A deliberately missing file produced a
failed row whose visible summary was `Command exited with code 2` (26 characters)
with the full output still collapsed; no successful row carried a summary, and the
Agent reported the missing file honestly instead of claiming success.
