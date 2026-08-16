# ADR 0021: Scoropic Dialogue Mode (Deferred)

## Status

Deferred.

## Context

The learner proposed a future dialogue-only mode modeled on the "Socratic
method applied to AI agents" idea (吴乐旻博士, Socratic questioning as a
learning product): through persistent Socratic questioning, the AI makes the
learner work out a concept themselves. This is a genuine pedagogical position,
distinct from the current problem-driven loop: the dialogue IS the lesson, not
a supplement to it.

## Decision

Record the idea; do not design or implement it now.

- It is a **dialogue-only mode**: no grading, no pull engine, no schedule — a
  conversation whose goal is the learner's own derivation of understanding.
- It must respect the existing boundaries when it is eventually designed:
  agent-native teaching (ADR 0020), no hard-coded pedagogy, traces recorded
  (learner answers in session traces), teacher conduct contract (no guessing,
  source citation).
- It is deferred because the v1 workbench loop (weakness → practice →
  feedback → explain/diagnose) must first prove itself in real study before a
  second, fully different interaction mode is designed.

## Consequences

The idea is preserved in the decision record, not lost to conversation. When
the main loop is stable, this ADR becomes the seed for a change proposal.
