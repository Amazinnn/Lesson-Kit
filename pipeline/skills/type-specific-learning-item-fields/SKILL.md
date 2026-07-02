# Skill: Type-Specific Learning Item Fields

Use type-specific internal fields only when they help the agent plan a clean Stage 1 source-reading guide.

Do not render these fields as student-facing labels.

## Required Output

Support:

```text
intermediate/first_pass/02_analysis/knowledge-points.md
intermediate/first_pass/03_plans/first-pass-structure-plan.md
```

## Base Internal Fields

Every required knowledge point needs these internal fields in `knowledge-points.md`:

```text
kp_id
source_unit_id
source_location
knowledge_item
knowledge_type
secondary_knowledge_type
source_form
learning_action
minimum_mastery_standard
dependency_kp_ids
related_kp_ids
deferrable
final_markdown_location
checkpoint_question
```

`related_kp_ids` is optional and should not be forced.

## Type-Specific Internal Hints

Use these only as internal planning hints, not as required student-facing fields:

- `concept-property`: underlying object, key condition, adjacent concept, representation, boundary/counterexample.
- `method-modeling`: applicable object, selection condition, modeling first move, boundary, comparison target.
- `formula-calculation`: variable roles, use conditions, meaning of the relation, formula group, boundary case.
- `algorithm-process`: input condition, state/field role, one-round action, stop condition, failure condition.
- `code-implementation`: interface, core variable, loop condition, boundary input, memory/array role, debugging observation.
- `system-timing`: module/signal/state, table or waveform location, trigger condition, transition, observation target.
- `lab-implementation`: goal, artifact/tool, operation step, expected observation, verification evidence, troubleshooting cue.
- `memory-recall`: recognition cue, grouping cue, adjacent/confusing item, recall prompt.

## Stage 1 Boundary

Do not add advanced review-system fields such as `review_priority`, `graph_role`, `confusion_pairs`, or `reuse_tags` to Stage 1 templates.

Do not create student-facing cards with status, time spent, confidence, progress, or workflow labels.

The final `速览` should render knowledge directly as a clean definition/formula statement plus a through-line accent sentence and a checkpoint question.
