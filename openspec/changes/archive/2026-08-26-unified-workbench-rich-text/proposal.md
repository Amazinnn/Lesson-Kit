# Unified workbench rich text

The workbench currently renders Markdown differently in server pages, practice cards, graph details, and Agent messages. This change defines one small, safe Markdown subset and applies it to all user-visible learning text without adding a dependency.

## Scope

- Render headings, paragraphs, ordered/unordered lists, blockquotes, fenced/inline code, emphasis, safe links, wiki links, math, and workspace-local images.
- Escape raw HTML and reject unsafe links and image paths.
- Coalesce Agent text events before rendering.

## Non-goals

- No Markdown library, build step, or new public API.
- No change to learning writes, routes, or provider behavior.
