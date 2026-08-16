# ADR 0015: Cascade Signal Boosts

## Status

Accepted.

## Context

Proof-heavy courses (discrete mathematics, physics) revealed a single-point
signal model blind spot: a weak downstream knowledge point (pigeonhole
principle) often has weak foundations upstream (counting, set theory), but
single-point ordering never surfaces the foundations. The learner's own
diagnosis matches: "core knowledge points are few and memorizable, but the
proof ideas never materialize."

## Decision

Add **query-time derived boosts** to weak-point ordering, layered on top of the
evidence signals from ADR 0008/0010:

- Along `prerequisite` (source precedes target), `applies_to` (source is a
  method of target), and `part_of` edges, a signaled knowledge point boosts its
  reverse-direction neighbors.
- Depth ≤ 2 hops; decay 0.5 per hop; weighted by relation strength
  (high 1.0 / medium 0.7 / low 0.4).
- `learner_signals` remains evidence-only: cascades never create or mutate
  signal rows. Boosts are computed at query time and displayed with their
  reason ("raised because downstream X is weak").
- `contrasts`, `variant_of`, and `generalizes` do not cascade — they drive
  related review (ADR 0019), not foundation repair.

## Consequences

Weak foundations surface exactly when the learner needs them, without polluting
the evidence model. Ordering remains explainable. Cost: one bounded graph walk
per weak-list computation, negligible at pool scale; the derivation lives in
the learning-model layer as a pure function and is unit-testable.
