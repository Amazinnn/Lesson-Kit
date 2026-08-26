# Workbench rich text

## ADDED Requirements

### Requirement: User-visible Markdown uses one safe subset
All user-visible learning text SHALL use the same supported Markdown subset: ATX headings through level 3, paragraphs, ordered and unordered lists, blockquotes, fenced and inline code, strong/emphasis, safe http(s) links, wiki links, math, and workspace-local images.

#### Scenario: Agent answer renders Markdown
- **WHEN** an Agent or student message contains `##`, `**bold**`, a list, or a fenced code block
- **THEN** the message displays semantic headings, emphasis, list markers, and code styling rather than raw Markdown syntax

#### Scenario: Unsafe markup is rejected
- **WHEN** text contains raw HTML, a `javascript:` link, or an image path outside the workspace figure directory
- **THEN** the rendered output contains escaped text and no executable link or image

### Requirement: Streaming text is one message
Partial Agent text events SHALL update one assistant message until the turn completes.

#### Scenario: Partial events coalesce
- **WHEN** a turn emits several text events
- **THEN** the UI shows one growing assistant message and renders the combined Markdown
