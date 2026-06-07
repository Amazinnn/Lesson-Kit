# Gate: Workflow Update Gate

Pass only if a workflow change moves each affected rule into an appropriate current file, logs useful session design ideas even when they are not implemented yet, updates routing or file contracts when needed, avoids preserving obsolete file shells as runtime paths, updates rule migration notes when V14 coverage is affected, and updates `CHANGELOG.md` for durable workflow or packaging changes.

Fail if `CHANGELOG.md` is missing from the root package.

Fail if a workflow-design discussion produced durable judgments, promising field/file ideas, stage-boundary decisions, naming proposals, unresolved alternatives, or risk warnings and none of them were logged.
