# ADR 0006: Rich Editable Graph Prototype

## Status

Accepted.

## Context

ADR 0005 kept the editable graph small: Python standard library server,
dependency-free static preview, and narrow pool mutations. That boundary made
the first local maintenance surface easy to run, but it cannot support the next
learning-workflow needs:

- reliable LaTeX rendering for problem text and knowledge notes;
- map-like force layout with readable node spacing;
- Typora-style editing for Markdown and math-heavy notes.

The project is expected to be rewritten later with a fuller front end and back
end. The current implementation should therefore be a migration-friendly MVP,
not a final Python-template UI.

## Decision

Keep the static Knowledge Graph Preview lightweight and read-only.

Upgrade only the localhost Editable Graph View into a rich local prototype
served from built front-end assets. The local server remains scoped to the
active course and chapter, and the editable view may still update only:

- knowledge-point body text;
- fragile notes;
- durable problem progress and attempts.

Expose graph data through a JSON API so the front end does not depend on
server-generated HTML. The editor saves Markdown/LaTeX source text back to the
pool, never rendered HTML.

## Consequences

The editable graph can use mature front-end libraries for math rendering,
force-directed layout, and Markdown editing without turning the static preview
into a heavy artifact.

The repo now has a small front-end build step for maintainers. Built assets are
checked in so ordinary local use does not require Node.

This creates a clearer migration path for a future full web application: keep
the graph JSON shape, mutation endpoints, and source-text save semantics stable
while replacing the temporary Python server later.
