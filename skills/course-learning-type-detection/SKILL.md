# Skill: Course Learning Type Detection

Detect each knowledge point's `knowledge_type` by the action expected from the student, not by course name alone.

## Required Output

Support `intermediate/first_pass/02_analysis/knowledge-points.md`.

Use:

```text
knowledge_type
secondary_knowledge_type
source_form
```

## Knowledge Types

Use one primary `knowledge_type` and optional `secondary_knowledge_type`:

- `concept-property`: definitions, properties, boundaries, representation conversion.
- `method-modeling`: choosing a method and turning a problem into a model.
- `formula-calculation`: variables, conditions, formulas, computation meaning.
- `algorithm-process`: states, fields, one-round updates, correctness conditions, complexity.
- `code-implementation`: interfaces, variables, loops, memory, boundary inputs, debugging observations.
- `system-timing`: modules, signals, states, tables/diagrams, timing, waveforms.
- `lab-implementation`: goal, design, implementation, simulation, board/test evidence, troubleshooting.
- `memory-recall`: recognition, recall, spaced review, confusion pairs.

Use `secondary_knowledge_type` only when the source item genuinely combines two learning actions. Do not add a secondary type merely for symmetry.

## Source Form

Use `source_form` for how the source presents the item, such as:

```text
concept
theorem
condition
method
analysis_pattern
algorithm_step
code_statement
visual_interpretation
lab_operation
implementation_step
verification_action
```

`source_form` is not a substitute for `knowledge_type`.

## Student Actions

Record likely actions in `learning_action`, such as recognize, explain, judge, model, trace, identify condition, identify boundary, identify variable role, identify step role, or recall.

For Stage 1, avoid actions that imply full execution: compute, prove, implement, debug, or operate should be deferred unless they are only being recognized as source structure.

## Rule

The learning type changes the intermediate rendering plan and checkpoint question target. It must not appear as a label in the student-facing final `速览`.
