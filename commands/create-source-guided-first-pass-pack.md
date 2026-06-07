# Command: Create Source-Guided First-Pass Lesson

Use this command when the user has source material and needs a source-grounded first-pass lesson. The final artifact is a Markdown file named with this pattern:

```text
（科目名） （第X章） （章名） 速览.md
```

This command does **not** create a formal lesson note, a chapter summary, a formal problem set, an answer key, an exam-prep guide, a review system, a knowledge graph, or a timed learning-session plan.

## Harness Position

The first-pass intermediate files are agent-facing harness contracts. They are not student-facing notes. They exist to lock source boundaries, register the full knowledge-point inventory, plan final rendering, audit coverage, and force repair at the earliest broken layer.

## Required Load List

Always read before executing this command:

```text
START_HERE.md
RED_LINES.md
FILE_CONTRACT.md
STYLE.md
skills/source-and-scope/SKILL.md
skills/intermediate-contracts/SKILL.md
skills/source-material-type-detection/SKILL.md
skills/course-learning-type-detection/SKILL.md
skills/first-pass-learning-item-extraction/SKILL.md
skills/learning-item-granularity/SKILL.md
skills/type-specific-learning-item-fields/SKILL.md
skills/checkpoint-question-generation/SKILL.md
skills/first-pass-pack-rendering/SKILL.md
gates/first-pass-pack-quality-gate.md
gates/source-grounding-gate.md
gates/learning-item-granularity-gate.md
gates/question-specificity-gate.md
gates/section-order-gate.md
gates/no-summary-substitution-gate.md
gates/format-rendering-gate.md
skills/knowledge-relationship-analysis/SKILL.md
templates/intermediate/first_pass/02_analysis/knowledge-relationship-analysis-template.md
skills/kp-consolidation-analysis/SKILL.md
templates/intermediate/first_pass/02_analysis/kp-consolidation-analysis-template.md
```

If the source is PDF or image-based, also read:

```text
skills/pdf-visual-reading/SKILL.md
gates/pdf-reading-gate.md
```

If the source is PPT or PPTX, also read:

```text
skills/ppt-source-handling/SKILL.md
gates/ppt-visual-reading-check.md
```

If the source contains diagrams, figures, tables, circuit diagrams, state diagrams, waveforms, or other visual-dependent content, also read:

```text
gates/visual-dependency-check.md
```

If the chapter is lab/system/implementation-heavy, also read:

```text
gates/lab-implementation-field-check.md
```

## Entry Conditions

Use this command when the user wants to begin reading a chapter or source material and needs a source-guided first-pass lesson such as:

- “Create a first-pass lesson for this chapter.”
- “Generate a source-guided first-pass lesson.”
- “Help me read the PPT/PDF with grounded knowledge points.”
- “Build the full knowledge-point inventory first, then generate the first-pass lesson.”

Do not use this command when the user asks for:

- a formal lesson note;
- a full chapter summary;
- a formal exercise set;
- an answer key;
- exam review compression;
- feedback-driven lesson revision.

## Required Sequence

1. Create the first-pass four-layer workspace:

```text
intermediate/first_pass/01_inputs/
intermediate/first_pass/02_analysis/
intermediate/first_pass/03_plans/
intermediate/first_pass/04_checks/
```

2. Lock source scope in `intermediate/first_pass/01_inputs/source-scope.md`.
3. Build the mandatory full knowledge-point inventory in `intermediate/first_pass/02_analysis/knowledge-points.md`.
3.1. Analyze textbook exercises for embedded knowledge points: identify exercises that contain extension KPs (transferable patterns, boundary techniques, cross-domain connections, or practical supplements) and register them in the Exercise-Derived KPs section of `knowledge-points.md`. Use `example-exercise-inventory.md` (when triggered) as input evidence.
3.2. Run KP consolidation analysis in `intermediate/first_pass/02_analysis/kp-consolidation-analysis.md`: evaluate each knowledge point for scene-judgment MCQ viability, merge KPs that cannot support independent scene-judgment questions, and document the merged structure.
3.5. Analyze knowledge relationships in `intermediate/first_pass/02_analysis/knowledge-relationship-analysis.md`: identify relation types between knowledge points, select 1-2 through-line perspectives that recur across the chapter. These perspectives will inform the `quick_absorption` field in the structure plan.
4. Ensure every source-required item becomes a learnable unit with a V17 `knowledge_type`, optional `secondary_knowledge_type`, and `source_form`.
5. Create triggered inventory files only when the required harness spine cannot safely express the source structure.
6. Plan final rendering in `intermediate/first_pass/03_plans/first-pass-structure-plan.md`.
7. Run source and knowledge coverage in `intermediate/first_pass/04_checks/coverage-check.md`.
8. Repair the earliest broken layer before final rendering. Do not patch only the final Markdown.
9. Render the final Markdown first-pass lesson using `skills/first-pass-pack-rendering/SKILL.md`, `STYLE.md`, and `templates/first-pass/first-pass-lesson-template.md`.
10. Re-run `gates/first-pass-pack-quality-gate.md`, `gates/no-summary-substitution-gate.md`, and `gates/format-rendering-gate.md` before export.

## Output File Checklist

Always create or update:

```text
[ ] intermediate/first_pass/01_inputs/source-scope.md
[ ] intermediate/first_pass/02_analysis/knowledge-points.md
[ ] intermediate/first_pass/02_analysis/knowledge-relationship-analysis.md
[ ] intermediate/first_pass/02_analysis/kp-consolidation-analysis.md
[ ] intermediate/first_pass/03_plans/first-pass-structure-plan.md
[ ] intermediate/first_pass/04_checks/coverage-check.md
```

Create only when triggered:

```text
[ ] intermediate/first_pass/01_inputs/visual-inventory.md                 if visual-dependent content cannot be audited inside the core harness files
[ ] intermediate/first_pass/01_inputs/code-algorithm-inventory.md         if code/pseudocode/algorithm traces cannot be audited inside the core harness files
[ ] intermediate/first_pass/01_inputs/lab-artifact-inventory.md           if implementation chains cannot be audited inside the core harness files
[ ] intermediate/first_pass/01_inputs/example-exercise-inventory.md       if source examples/exercises materially define required first-pass knowledge points
[ ] intermediate/first_pass/04_checks/ppt-visual-reading-check.md         if source is PPT/PPTX
[ ] intermediate/first_pass/04_checks/visual-dependency-check.md          if visual-dependent content exists
[ ] intermediate/first_pass/04_checks/lab-implementation-field-check.md   if lab/system implementation items exist
```

Final artifact:

```text
[ ] （科目名） （第X章） （章名） 速览.md
```

## Blockers

Stop before rendering the final first-pass lesson if:

- source scope is not locked;
- full coverage claim is unclear;
- `knowledge-points.md` is missing or incomplete;
- knowledge relationships are not analyzed before structure planning;
- KP consolidation analysis is not run before structure planning;
- source-required content is not registered as knowledge points;
- knowledge points are broad headings rather than learnable units;
- knowledge points lack source locations;
- knowledge points lack `knowledge_type`, `source_form`, learning actions, minimum mastery standards, final Markdown locations, or checkpoint questions;
- textbook/PPT/teacher-required content is marked deferred;
- the final structure is not grounded in knowledge-point IDs;
- coverage check is missing source coverage matrix or knowledge landing matrix;
- the final artifact reads like a chapter summary, mini-lesson, problem set, formalistic template, exam-prep guide, answer routine, scoring rubric, drill sheet, or timed learning-session plan;
- the final artifact displays `kp_id`, source locations, `knowledge_type`, `writing_view`, `rendering_intent`, template labels, or other internal fields;
- checkpoint questions require calculation, proof, code writing, real operation, or can be answered from the short statement alone without returning to the source;
- short explanations lack application conditions when conditions exist;
- short explanations lack multi-angle interpretation when the item benefits from multiple angles;
- gate failures are patched only in final Markdown instead of the broken intermediate layer.
