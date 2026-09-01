# Change: Establish typography content boundaries

## Why

Primary learning text must remain readable at arbitrary title length, while code,
mathematics, and tables must not widen the middle or Agent column. Several surfaces
already handle one of these cases, but the rule is not consistently applied to their
flex and grid parents.

## What Changes

- Give major flex and grid children permission to shrink.
- Wrap user-authored titles, questions, notes, and primary knowledge labels in place.
- Keep inline code breakable and make preformatted code, display mathematics, and
  tables scroll within their own surface.
- Remove ellipsis from practice-scope and suggestion knowledge titles.

No content is truncated or rewritten.
