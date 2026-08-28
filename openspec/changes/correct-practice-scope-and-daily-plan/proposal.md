## Why

The archived daily-learning-plan change described useful presentation ideas but
left an unsafe ambiguity: practice could still be interpreted as pulling from
weak items or a whole pool, and a plan could be read as inventing a course goal
or a detailed task list. This correction makes the knowledge view the explicit
scope boundary and keeps plan output grounded in real data.

## What changes

- Knowledge graph and knowledge list share one explicit, tab-scoped selection.
- A practice start requires a non-empty selected scope and exactly one mode.
- An Agent may replace that selection only after an explicit practice intent;
  ordinary conversation cannot alter it.
- No-scope practice is an empty handoff state. Weak-point ordering remains a
  display aid and never becomes an implicit pull source.
- Long-term and stage goals render as independent cards backed by real goals.
  Today's plan is a separate coarse queue capped at three items; it never
  fabricates a course goal, duration, mastery, or micro-action checklist.
- Flash Card and Yes-No remain supported contract modes only when explicit
  content metadata makes them available; they are not declared implemented by
  this documentation change.

## Scope and compatibility

This is a documentation/OpenSpec correction for the workbench changes that
follow. It preserves existing learning-write APIs, session-storage semantics,
the Shell → Domain → Data layering, and all archived change directories.
Implementation work is separately tracked in the task list and must not alter
pipeline, pool scripts, lessonkit.py, or external Agent CLI behavior.

