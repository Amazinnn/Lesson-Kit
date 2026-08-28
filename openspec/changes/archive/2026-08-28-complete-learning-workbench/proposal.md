## Why

The workbench now has a reliable structural graph, explicit knowledge selection,
continuous exam practice, native Agent conversations, and a deterministic daily
queue. Several visible entry points are still only contract shells: Flash Card
and Yes/No have no production content, unified self-rating is unreachable from
the current start card, goals cannot be entered, and Agent selection/planning
cannot affect the browser state.

## What changes

- Separate content mode (`exam`, `flash_card`, `yes_no`) from rating mode
  (`immediate`, `batch`) and require one value from each before a session pulls.
- Render optional structured choices when content supplies them; never infer
  Flash Card or Yes/No from an old problem type.
- Add a small local goal store and goal CRUD endpoints, refresh the whole plan
  region after recalculation, and keep the deterministic planner as fallback.
- Add an explicit Agent action envelope that can replace the current selected
  knowledge-point scope only when the user requested practice.
- Add list sorting and a small graph projection selector for existing metrics;
  preserve the structural graph as the default and keep all selection semantics.
- Keep calendar, workload curve, model selection, dynamic third-party plugin
  installation, cross-disciplinary views, and automatic AI question generation
  as documented future work rather than fake controls.

## Scope and compatibility

All changes stay under `workbench/` plus approved incremental migration code,
tests, OpenSpec, and docs. Shell -> Domain -> Data remains one-way; Content is
read-only; Bridge is beside the core. Existing JSON APIs and learning-write
request shapes remain compatible. New goal and Agent action endpoints are
additive. No pipeline, pool script behavior, lessonkit.py behavior, or external
Agent CLI command is changed.

