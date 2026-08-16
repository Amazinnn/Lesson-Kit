# ADR 0010: Pain-Point-First Scheduling

## Status

Accepted.

## Context

The learner's study principle is to work their own pain points: repeatedly
practice what they do not know, in the mode they are worst at — a hard problem
means practice that problem; a missing calculation method means practice that
calculation. Classic spaced-repetition schedulers (Anki-style) lock items until
their due date, which contradicts "practice it now". The learner explicitly
rejected fixed session flows ("read cards first, then answer, then see the
solution"). Evidence from use: the material was created (303 problems) but
practice stopped at 2 attempts — friction, not knowledge, killed the loop.

## Decision

The forgetting curve is a **background reminder, never a lock**:

- Weakness ordering drives what the learner sees: `signal weight × due boost ×
  in-session repeat penalty`. Signals come from `learner_signals`; due state
  from a new `review_schedule` table.
- Every item stays reachable at all times. Due dates only raise an item's
  order and appear as reminders; they never hide, lock, or refuse an item.
- A lightweight SM-2 variant maintains repetitions, ease, interval, and due
  date per item (kp or problem) in `review_schedule`.
- Sessions are flow-free: the learner can start from the weak list, from due
  reminders, from a specific problem, or from a knowledge point.

## Consequences

The tool respects the learner's own study behavior instead of imposing a
schedule. The curve still guards against the classic failure it exists for:
"thought I knew it, actually forgot it" — forgotten items rise in order when
their due date passes. The scheduling engine stays simple (a pure function of
results and time) and can be unit-tested without a UI.
