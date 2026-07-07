# ADR 0005: Local Editable Graph View

## Status

Accepted.

## Context

Lesson-Kit's static graph preview is useful for reading the knowledge map, but
study maintenance needs two write actions close to the graph:

- revise a knowledge point's body or fragile note while reviewing it;
- record durable problem progress while practicing linked problems.

The normal extraction pipeline remains the auditable path for creating and
structuring knowledge assets. However, learning notes and practice state are
live maintenance data. Forcing every small note through extraction artifacts
would make the workflow too heavy.

## Decision

Add a localhost-only editable graph mode backed by the course SQLite pool.

The editable graph may update only:

- `knowledge_points.body`;
- `knowledge_points.fragile`;
- current and historical durable problem progress.

It may not create or delete knowledge points, edit relationships, edit problem
text, or edit solutions. The static graph renderer remains read-only and
dependency-free.

The server uses Python standard library only and binds to `127.0.0.1` by
default. It is a local maintenance surface, not a public web app.

## Consequences

Learning notes can enter the pool at the moment they are discovered.

The SQLite pool becomes the source of truth for post-extraction notes and
problem progress, while intermediate extraction files remain the audit trail
for initial asset creation.

Because the editable graph mutates the pool, it must stay explicitly scoped.
If Lesson-Kit later needs full CRUD, multi-user access, auth, or sync conflict
handling, that should be designed as a separate application boundary rather
than extending this localhost maintenance mode.
