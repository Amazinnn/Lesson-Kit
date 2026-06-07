# Knowledge Points

| kp_id | source_unit_id | source_location | knowledge_item | knowledge_type | secondary_knowledge_type | source_form | learning_action | minimum_mastery_standard | dependency_kp_ids | deferrable | final_markdown_location | checkpoint_question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| course-source-ch03-kp-001 | su-001 |  |  | concept-property / method-modeling / formula-calculation / algorithm-process / code-implementation / system-timing / lab-implementation / memory-recall | optional secondary type | concept / theorem / condition / method / analysis_pattern / algorithm_step / code_statement / visual_interpretation / lab_operation / implementation_step / verification_action |  |  |  | no / extension_only |  |  |

## Knowledge Point ID Rule

`kp_id` must be unique beyond a single chapter when the workflow may feed knowledge graphs, review files, weak-point tracking, or cross-book reuse.

Use a namespaced ID that includes enough course/source/chapter scope to prevent collisions. Current examples are placeholders for the namespaced direction, not the final naming grammar:

```text
course-source-ch03-kp-001
```

The exact namespace tokens may be shortened for readability, but they must be stable within the project and sufficient to prevent cross-chapter and cross-book collision.

Do not display `kp_id` in the student-facing final artifact. Preserve it in intermediate files and later-stage mapping files.

## Knowledge Type Rule

Use `knowledge_type` for the primary learning action required by the knowledge point. Choose from:

```text
concept-property
method-modeling
formula-calculation
algorithm-process
code-implementation
system-timing
lab-implementation
memory-recall
```

Use `secondary_knowledge_type` only when the source item genuinely combines two learning actions. Do not add a secondary type merely for symmetry.

Use `source_form` for the source-material form, such as concept, theorem, condition, algorithm step, code statement, visual interpretation, lab operation, implementation step, or verification action. `source_form` is not a substitute for `knowledge_type`.

## Required Content Rule

Textbook/PPT/teacher-required content must be registered here before final Markdown writing. It may not be omitted, hidden as deferred, or replaced by a broad chapter heading.

Extension content may be registered as `extension_only`, but it must not become required first-pass mastery unless source evidence requires it.

## Learnable Unit Rule

Each `knowledge_item` must be a learnable unit. A learnable unit may be a concept, theorem, condition, method, analysis pattern, algorithm step, code statement, visual interpretation, lab operation, implementation step, or verification action.

This file fails if it only lists headings, broad topics, chapter conclusions, or summary statements.

## Knowledge Relation Rule

Use `dependency_kp_ids` for strict prerequisite relations: knowledge points that must be understood before this item can be read safely.

Do not add advanced review-system fields such as `review_priority`, `graph_role`, `confusion_pairs`, or `reuse_tags` to Stage 1. Those belong to later lesson/review loops when feedback, practice, or a dedicated graph design exists.

## Final Markdown Binding Rule

Every required `kp_id` must have a planned `final_markdown_location` before final rendering. The final first-pass lesson must not display `kp_id`; traceability is preserved through this inventory, `first-pass-structure-plan.md`, and `coverage-check.md`.

## Minimum Completion Standard

This file fails if any required source unit lacks knowledge-point coverage, if any knowledge point lacks source location, `knowledge_type`, `source_form`, learning action, minimum mastery standard, final Markdown location, or checkpoint question, or if required source content is marked deferrable.

## Exercise-Derived Knowledge Points

Some textbook exercises contain knowledge that extends beyond direct application of body material. These are not alternative practice for existing KPs — they are independent learnable units embedded in exercises.

### Identification Criteria

An exercise contains a new KP when it satisfies **any** of the following:

| Criterion | Meaning | Example |
|-----------|---------|---------|
| transferable_pattern | Exercise reveals a strategy/method applicable to other similar problems beyond this specific exercise | A general approach for constructing auxiliary curves when applying Green's theorem |
| boundary_technique | Exercise demonstrates a technique for cases where a theorem's standard conditions are not met | Handling singularities by removing small regions |
| cross_domain_connection | Exercise connects this chapter's concept to a concept from another domain | Relating Green's theorem to physical circulation |
| extension_supplement | Exercise extends a body concept with practical variations not mentioned in the source | ROM capacity expansion methods beyond what the body text covers |

Exercise content that is straightforward application (even if it requires creativity) does NOT qualify as a new KP.

### Registration Format

Exercise-derived KPs appear in a separate section of this file:

```
## Exercise-Derived KPs

| kp_id | source_exercise | knowledge_item | knowledge_type | exercise_kp_type | linked_body_kp_ids | source_form |
|-------|----------------|----------------|----------------|------------------|--------------------|-------------|
| course-source-ch03-kp-015 | ex-10.5 | ROM capacity expansion methods | method-modeling | extension_supplement | course-source-ch03-kp-010 | exercise_extension |
```

The `exercise_kp_type` indicates which criterion was met: `transferable_pattern` / `boundary_technique` / `cross_domain_connection` / `extension_supplement`.

The `source_form` for exercise-derived KPs is `exercise_extension` (distinct from body KPs' `concept` / `theorem` / etc.).

### Consumption by Later Stages

Stage 2 (lesson writing) conditionally loads this file. When present, it reads the Exercise-Derived KPs section and automatically includes those KPs in the lesson plan for explicit explanation. This ensures that exercise-embedded knowledge is not missed even when student feedback is incomplete.

Exercise-derived KPs appear in the 速览 (Stage 1) using the same format as body KPs: title + quick_absorption (formula/definition + interpretation + through-line) + scene-judgment MCQ. The MCQ tests the conceptual understanding of the extension, not the exercise-specific details.
