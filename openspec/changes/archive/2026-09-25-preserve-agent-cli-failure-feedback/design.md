# Design

## Evidence and smallest fix

Observed command:

```text
python -m workbench.cli.main data create kp 2>&1 | head -20
```

Correct shape:

```text
lesson-kit data <workspace> create kp --input <file>
```

Argparse emits usage/error on stderr and exits 2. Business errors from data,
difficulty, and ingest generally emit JSON on stdout and also exit 2. Shell
pipelines can replace the CLI exit status with the final command's status.
Pi normalization currently trusts `isError`; full output is collapsed.

Keep these error mechanisms. Add accurate prompt examples using the current
workspace, instruct help discovery before guessing flags, and require isolated
Lesson Kit invocations that retain their exit status. This guidance does not
constitute a shell sandbox: if an Agent disregards it, output text alone cannot
reliably reconstruct a masked exit code.

For a provider-reported failed activity, derive a short summary from its
sanitized output (maximum 240 characters) and render it outside the disclosure.
Use a generic failure message if output is empty. Redact before truncating and
storage, reuse existing helpers, and never scan successful output to decide
whether a call failed. Keep the full bounded output collapsed by default.

Tool failure does not automatically fail the entire conversation: the Agent may
consult help and issue a corrected call. Keep each invocation's activity id and
outcome distinct; report an operation as successful only after a successful
result. Existing successful-turn-only transcript persistence remains in force.

## Delivery boundary

This handoff creates documentation only. The receiving Agent implements and
tests the change. Use temporary fixtures or an isolated workspace; do not write
to real learning pools, commit, or push without separate authorization.
