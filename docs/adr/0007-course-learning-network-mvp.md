# ADR 0007: Course Learning Network MVP

## Status

Accepted.

## Context

Lesson-Kit could eventually become a broader learning system where any life
artifact can become a lesson. That direction is attractive, but the current
product already has a concrete, useful spine:

- source material is extracted into course-scoped knowledge points;
- durable problems attach to those knowledge points;
- the graph preview and editable graph make the pool visible and maintainable.

The next useful step is to make relationships between knowledge points first
class. At the same time, not every discovered relationship should become a
stored edge. A shortest path, a shared neighbor, or a dense cluster is often a
query-time graph finding rather than an audited source fact.

## Decision

Build the Course Learning Network as a course-specific MVP before designing a
generic life knowledge map.

Add a durable low-level relation layer:

- `knowledge_relations` stores audited point-to-point edges;
- relation manifests import only reviewed relationships;
- legacy `related_kp_ids` remains a fallback for older pools.

Add a lightweight query-time exploration layer:

- Signal Map records learner-specific weak spots and relation gaps;
- Focus Map outputs compact JSON around seed nodes, optional target paths,
  shared neighbors, simple clusters, and graph findings;
- Focus Map does not generate HTML and does not persist inferred
  relationships.

## Consequences

The current course workflow becomes more useful without turning the repo into a
large graph platform.

Algorithmic discoveries stay reversible and contextual. If a generated path or
suspected relation proves valuable, it can later be audited into
`knowledge_relations`.

The future generalization path remains open: the Course Learning Network can be
treated as the first validated specialization of a broader Lesson-Kit model.
