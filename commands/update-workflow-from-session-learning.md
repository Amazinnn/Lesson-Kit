# Command: Update Workflow From Session Learning

Use this command when a discussion reveals a durable workflow rule, failure pattern, packaging change, or runtime wayfinding problem.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
TASK_ROUTER.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
CHANGELOG.md
skills/quality-audit/SKILL.md
gates/workflow-update-gate.md
```


## Sequence

1. Record the session learning as a plain rule change request.
2. Decide whether it affects routing, commands, skills, gates, templates, style, or changelog.
3. Move the rule into the proper current file. Do not keep old file shells merely to preserve wording.
4. Update `CHANGELOG.md` for every durable workflow version change, rule-preservation patch, packaging change, or runtime/contract change.
6. Run a consistency check against `START_HERE.md`, `TASK_ROUTER.md`, `RED_LINES.md`, `FILE_CONTRACT.md`, and `CHANGELOG.md`.

## Session Design Log Rule

During workflow-design discussions, record useful ideas as soon as they appear. Do not wait until they have been implemented.

Log entries should include durable design judgments, promising field or file ideas, risk warnings, stage-boundary decisions, naming proposals, and unresolved but potentially valuable alternatives.

Each entry should state its status:

```text
locked        already part of the current workflow rule set
to-implement  accepted direction, not yet moved into runtime files/templates/gates
to-verify     useful hypothesis that needs sample testing
parked        not adopted now, but preserved with rationale
risk          warning meant to prevent later misuse or drift
```

When a logged idea changes runtime behavior, file contracts, gates, templates, packaging, or rule preservation, also update the affected current files and `CHANGELOG.md`.

## Output File Checklist

```text
[ ] useful session design ideas logged even when not implemented yet
[ ] affected runtime files updated
[ ] affected templates/gates/skills updated when needed
[ ] CHANGELOG.md updated
[ ] workflow update gate passed or manual review note written
```

## Rule

Rule preservation is about preserving obligations, blockers, and decisions, not preserving obsolete file names.

## Changelog Rule

`CHANGELOG.md` is unconditionally preserved as a current root log. Do not delete it during simplification. If a change is important enough to affect workflow behavior, routing, files, gates, packaging, or rule preservation, record it there.
