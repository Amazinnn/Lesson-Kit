# Change: Complete linked-problem summaries

## Why

Linked problems currently display the first 56 characters of the problem text and append an ellipsis. That is neither a real summary nor a complete question, and it obscures the exact content a learner may choose to open.

## What Changes

- Add optional durable display summaries to formal and candidate problems.
- Generate summaries only for normalized problem text longer than 300 characters.
- Render a concise title, an optional complete summary, and an expandable full problem statement without truncation or raw ids.
- Track the reviewed dmath display metadata in a reproducible sidecar manifest.

## Capabilities

- `workbench-ui`

## Impact

Additive SQLite columns, server-rendered linked-problem markup, CSS, metadata import, and tests. No route or learning-record behavior changes.
