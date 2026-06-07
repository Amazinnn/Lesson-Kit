# Skill: Knowledge Relationship & Through-Line Analysis

Analyze relationships between knowledge points from the knowledge-points inventory and identify through-line perspectives for the quick_absorption field.

## Required Inputs

```text
intermediate/first_pass/02_analysis/knowledge-points.md
```

## Required Output

Write `intermediate/first_pass/02_analysis/knowledge-relationship-analysis.md`.

## Analysis Rules

### 1. Build the Relationship Matrix

For each pair of knowledge points that have a meaningful relationship in the source material, record:
- **Relation Type**: Choose from the 14 types in the template (analogy, contrast, prerequisite, etc.)
- **Direction**: Is the relationship directional (A→B, A←B) or bidirectional (A↔B)?
- **Strength**: How strong is the connection? (high/medium/low)
- **Cognitive Function**: What cognitive operation does this relationship support? (scaffolding, elaboration, comparison, integration, transfer)
- **Manifestation Level**: Where does this relationship manifest? (reading, problem-solving, review, cross-chapter)
- **Cross-Section**: Does it span within a subsection, within a section, or across sections/chapters?
- **Co-occurrence Frequency**: How often do these two KPs appear together in the source? (always, often, sometimes, rarely)
- **Traceability Basis**: Is the relationship explicit in the source, implied, or a pedagogical design choice?

### 2. Identify Through-Line Perspectives

From the relationship matrix, identify 2-3 candidate perspectives that could serve as unifying angles:

- Each perspective must span at least 3 knowledge points across different sections
- Evaluate each candidate on: coverage ratio, recurrence count, pedagogical value, complexity, and risk
- Document non-selected candidates with reasons

### 3. Select and Justify

Choose 1-2 perspectives to serve as the through-line for quick_absorption fields:
- The perspective should be naturally recurrent (students encounter it multiple times)
- It should not require explanation beyond what the source provides
- It should serve later stages (lesson_loop, problem_set) without forcing them

## Perspective Type Guidance

| Perspective Type | When to Use | Example |
|-----------------|-------------|---------|
| recurring_operation | Same formula/operation pattern repeats | Every transformation theorem involves replacing P,Q with partial derivatives |
| dimension_evolution | Content naturally progresses low→high dimension | Line→surface→volume integrals |
| condition_tracking | A condition appears with different requirements | Orientation conditions differ between Green, Gauss, Stokes |
| structural_parallel | Multiple KPs share analogous structure | All three transformation theorems have the form: boundary integral = region integral |
| conceptual_thread | A single concept weaves through the chapter | "Direction matters" in second-kind integrals |
| comparative_frame | Content invites comparison | Type-1 vs Type-2 integrals across the chapter |

## Completion Standard

This skill fails if:
- The relationship matrix does not cover the chapter's key cross-KP relations
- Fewer than 2 through-line candidates are proposed
- The selected perspective lacks pedagogical justification
- The quick_absorption entry point is vague or generic
