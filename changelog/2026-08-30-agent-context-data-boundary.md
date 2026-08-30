# Agent context data boundary

- Moved next-content-id SQL out of the Server context builder and into the
  Data-layer Pool, restoring the documented Shell-to-Data dependency boundary.
- Scoped flash-card and micro-quiz allocation hints to the active course and
  chapter so unrelated workspaces cannot advance one another's numbering.
- Kept readable suffix allocation correct after identifiers exceed three digits.
- Added Pool and Agent-context regression coverage.
