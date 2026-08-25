## Context

`_problem_summary()` currently derives secondary text by cutting normalized `problem_text` at 56 characters. The real pool has 303 formal problems; 62 exceed 300 normalized characters. The SQLite file is ignored by Git, so reviewed display metadata also needs a tracked source artifact.

## Decisions

1. Add nullable `display_summary` columns to `problems` and `candidate_problems` through the existing additive schema migration path.
2. A display summary is permitted only when normalized problem text is longer than 300 characters. It must be one complete Chinese sentence of at most 48 characters and contain neither `…` nor `...`.
3. Linked rows always show the short title. A valid persisted summary is optional secondary text. An expandable disclosure renders the complete normalized problem statement; runtime substring summaries are removed.
4. `intermediate/dmath/problem_extraction/ch06/02_analysis/problem-display-metadata.json` is the reproducible source for the current title, topic, and optional summary values. Applying it is an explicit content operation, not a browsing event.
5. Raw problem ids remain absent from the linked-problem region.

## Migration and Validation

- Existing rows default to NULL and remain readable.
- The real pool is re-counted before backfill. All metadata rows are checked for id coverage, threshold compliance, summary length, forbidden ellipses, and topic coverage.
- At least 30 long-problem summaries, covering every represented topic, receive a recorded human audit before the change is archived.
