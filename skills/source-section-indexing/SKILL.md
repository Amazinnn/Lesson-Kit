# Skill: Source Section Indexing

Build the source-order backbone for the first-pass pack.

## Required Output

Write `intermediate/first_pass/01_inputs/textbook-section-index.md`.

## Rules

- Preserve source section order.
- A section is the smallest order-preserving unit.
- Do not reorder sections for conceptual convenience.
- Inside a section, learning items may later be reorganized by learning logic.
- Record section title, source locator, page/slide range, inclusion status, and notes.
- For PPT/PPTX, use slide ranges and visible section markers. If a section boundary is inferred, mark it as inferred.
