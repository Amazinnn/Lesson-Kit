# Linked problem full reading

## Why

The current linked-problem row repeats a title, a truncated summary, and a second disclosure, which increases reading cost and still loses Markdown structure.

## What Changes

Replace the duplicated linked-problem title/summary/disclosure stack with a direct readable row: topic groups stay collapsed until opened, then each row shows its short title and complete rendered statement.

## Scope

- Keep `display_summary` as compatible metadata, but raise its eligibility threshold to more than 500 normalized characters.
- Do not render summaries, truncated excerpts, ellipses, or raw problem ids in the linked-problem area.
- Preserve existing routes, query payloads, and learning-record behavior.

## Non-goals

- No new problem fields, APIs, generation service, or learning writes.
