# Knowledge Relationship & Through-Line Analysis

## 1. Knowledge Point Relationship Matrix

| KP-A | KP-B | Relation Type | Direction | Strength | Cognitive Function | Manifestation Level | Cross-Section | Co-occurrence Frequency | Traceability Basis |
|------|------|---------------|-----------|----------|-------------------|---------------------|---------------|------------------------|-------------------|
| kp-001 | kp-002 | analogy / contrast / prerequisite / generalization-specialization / cause-effect / process-step / part-whole / condition-application / example-concept / temporal-sequence / hierarchical / transitional / extension | A→B / A←B / A↔B | high / medium / low | scaffolding / elaboration / comparison / integration / transfer | reading / problem-solving / review / cross-chapter | same_subsection / same_section / cross_section / cross_chapter | always / often / sometimes / rarely | source_explicit / source_implied / pedagogical_design |

### Relation Type Reference

| Type | Meaning | Example |
|------|---------|---------|
| analogy | Similar structure across different contexts | Green's theorem: closed curve → region; Gauss's theorem: closed surface → volume |
| contrast | Opposition or difference on the same dimension | Type-1 vs Type-2 line integrals: geometric quantity vs oriented coordinate increment |
| prerequisite | A must be understood before B | Parametrization is prerequisite for applying Green's theorem |
| generalization-specialization | A is a special case or generalization of B | Plane curve integrals generalize to space as three-component forms |
| cause-effect | A causes or enables B | Path independence condition → existence of potential function |
| process-step | A is the procedural predecessor of B | Building curve integral definition → parametrization → Green's theorem |
| part-whole | A is a component of B | Closed-curve orientation convention is part of Green's theorem conditions |
| condition-application | A is a precondition for B | P,Q continuously differentiable + C positively oriented → Green's theorem applicable |
| transitional | Knowledge flow turns or progresses here | From "computation" of curve integrals to "transformation" via Green's theorem |
| extension | B supplements or extends A without being required | Area formula as a corollary of Green's theorem, not core |

## 2. Through-Line Perspective Candidates

Based on the relationship matrix, identify patterns/themes that can serve as unifying angles across the chapter.

| Candidate ID | Perspective Name | Perspective Type | KPs Involved | Coverage Ratio | Recurrence Count | Pedagogical Value | Complexity | Risk | Recommendation |
|--------------|------------------|------------------|--------------|----------------|------------------|-------------------|------------|------|----------------|
| tl-001 | | recurring_operation / dimension_evolution / condition_tracking / structural_parallel / conceptual_thread / problem_solving_pattern / comparative_frame | N/M | N% | N | high / medium / low | single_layer / multi_layer | low / medium / high | ★★★★★ |

### Perspective Type Reference

| Type | Description | Suitable Disciplines |
|------|-------------|---------------------|
| recurring_operation | Same operation reappears across multiple KPs | Math, Physics (formula operation patterns) |
| dimension_evolution | Progression from lower to higher dimension | Math, Physics (integrals, field theory) |
| condition_tracking | A condition/constraint varies across contexts | Universal ("under what conditions does this hold") |
| structural_parallel | Multiple KPs share a structural template | Math (formula analogies), Programming (design patterns) |
| conceptual_thread | One core concept runs through the entire chapter | Theoretical subjects (conservation, field, state) |
| problem_solving_pattern | Evolution of problem-solving strategies | Applied subjects |
| comparative_frame | Multiple approaches compared within one framework | Comparative content |

## 3. Selected Through-Line Perspective

| Selected Candidate | Rationale | Affected KPs | quick_absorption Entry Point |
|-------------------|-----------|--------------|------------------------------|
| (selected candidate ID) | Pedagogical reason for choosing this perspective | (list KPs affected) | One-sentence example of how this KP's quick_absorption enters from the selected angle |

## 4. Cross-Section Relationship Notes (Optional)

For strong cross-section connections that inform the chapter-end summary design.

| Relationship Summary | Sections Involved | Value for Chapter-End Summary |
|---------------------|-------------------|-------------------------------|
| Green → Gauss → Stokes: three transformation theorems | 10-1, 10-2, 10-3 | Core skeleton for chapter summary comparison |

## Completion Standard

This file is complete when:
- The relationship matrix covers all significant cross-KP relations (at least identifying key chapter-level relationships)
- At least 2 through-line perspective candidates are proposed, each with sufficient metric support
- The selected perspective has a clear pedagogical rationale, and its quick_absorption entry points are actionable by the rendering skill
- Rejected or low-value perspectives record the reason for non-selection
