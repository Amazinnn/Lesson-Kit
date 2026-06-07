# Example Exercise Inventory

Use only when source examples or exercises materially define required first-pass knowledge points.

| example_id | source_location | source_kind | required_learning_signal | linked_kp_ids | handling_decision |
|---|---|---|---|---|---|
| ex-001 |  | worked_example / thinking_question / source_exercise |  |  | knowledge_points_update / final_checkpoint / exercise_kp_extraction |

## Identifying Exercise-Embedded KPs

An exercise contains an **extension KP** (handling_decision = exercise_kp_extraction) when it satisfies any of:
- **transferable_pattern**: Reveals a strategy applicable beyond this specific exercise
- **boundary_technique**: Demonstrates handling of non-standard conditions
- **cross_domain_connection**: Links this chapter's concept to another domain
- **extension_supplement**: Extends body concepts with practical variations

When an exercise is classified as exercise_kp_extraction, the extension KP must be registered in the Exercise-Derived KPs section of `knowledge-points.md`. Simple application exercises (even creative ones) do not qualify.

## Minimum Completion Standard

This file fails if it preserves examples or exercises without stating how they define or verify first-pass knowledge points, or if exercises containing extension KPs are not flagged for `knowledge-points.md` registration.
