# Skill: Coverage-First Problem Selection

Select problems from `problems[]` with coverage as the first priority.

Default behavior:

- Use `source_kind=textbook` unless the scope says otherwise.
- Select at least one problem for each available core KP before adding extra
  problems for already covered KPs.
- Preserve source/problem order when coverage allows it.
- Keep duplicate-looking problems if they are selected intentionally; duplicate
  removal is not a pool-ingestion responsibility.
- Do not generate supplemental problems in v1. Record uncovered KPs as gaps.

Student-facing output must not show `kp_id` or internal coverage labels.
