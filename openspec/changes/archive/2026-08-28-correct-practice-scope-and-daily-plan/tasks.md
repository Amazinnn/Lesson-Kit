- [x] Add shared graph/list selection and a `practice-selected` handoff without
      changing existing read-only navigation semantics.
- [x] Require non-empty scope and exactly one practice mode; remove implicit
      weak-item/full-pool pulls and mode fallback.
- [x] Add real-goal cards and a deterministic coarse queue capped at three
      items; keep no-goal output truthful and zero-write.
- [x] Permit Agent selection replacement only for explicit practice intent and
      preserve ordinary-conversation read-only behavior.
- [x] Add route, domain, API, and browser tests for empty scope, mode filtering,
      no fallback, deduplication, truthful goals, and queue handoff. Agent-driven
      replacement remains covered by the Agent bridge tests.
- [x] Run strict OpenSpec validation and the repository verification commands;
      record outputs in the Task 1 report.
