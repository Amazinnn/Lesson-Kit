# KP Consolidation Analysis

Evaluate each required knowledge point for scene-judgment MCQ viability. Merge KPs that cannot support a meaningful scene-judgment question into adjacent KPs.

## Scene-Judgment Viability Assessment

For each KP, evaluate against these dimensions:

| kp_id | knowledge_item | knowledge_type | MCQ_viability | MCQ_failure_reason | merge_candidate | merge_rationale | post_merge_effect |
|-------|---------------|---------------|--------------|-------------------|----------------|-----------------|-------------------|
| kp-NNN | item | type | viable / merge / split | reason code | kp-XXX | why this merge | expected presentation |

### MCQ_viability values

| Value | Meaning | When to use |
|-------|---------|-------------|
| viable | Can produce a meaningful scene-judgment MCQ | KP describes a concept with clear application boundaries, comparative features, or condition-dependent behavior |
| merge | Cannot support scene-judgment; merge into adjacent KP | KP is pure definition, isolated term, single condition, or descriptive listing without decision space |
| split | Too broad for one scene-judgment question; split into finer KPs | KP bundles multiple distinct scene-judgment-worthy concepts |

### MCQ_failure_reason codes

| Code | Meaning | Example |
|------|---------|---------|
| pure_definition | Pure concept listing, no application scenarios | "散度是P_x+Q_y+R_z" — only a formula, no decision to make |
| isolated_term | Single symbol/term without operational context | "rot F" definition — just notation, no scene to judge |
| memory_recall | Rote memory item, no judgment space | "教材把公式写成X还是Y" — trivial recall, not scene judgment |
| condition_listing | List of conditions without application contrast | "格林公式条件：P,Q连续偏导+C正向" — just conditions, no scenario |
| tool_definition | Intermediate concept only used by another KP | Parameterization as a tool for Green's theorem |
| no_contrast | No adjacent concept to contrast with | Isolated concept with no alternative to compare against |
| self_evident | Answer obvious from quick_absorption alone | The quick_absorption already contains the answer |
| trivial_judgment | Any MCQ would be too simple or tautological | "闭曲线积分用格林公式? A.是 B.否" — too trivial |

### merge_candidate selection rules

1. Prefer merging into the KP that *uses* this definition/term (prerequisite → consumer)
2. If no consumer exists, merge into the nearest KP in source order
3. If the source section has remaining KPs after merging, keep the section structure; if all KPs in a subsection merge out, the subsection collapses
4. A merged KP's source_location is preserved in the parent KP's notes for traceability

### Merge rationale types

| Type | Description | Example |
|------|-------------|---------|
| consumed_by | This term is only used as a component of a larger concept | "散度性质是解释高斯公式时的辅助概念" |
| prerequisite_embed | This prerequisite is too narrow to stand alone | "参数化公式只是格林公式计算步骤中的一环" |
| definition_embed | This definition is only meaningful within its theorem | "二阶偏导连续是使用格林公式的前提条件" |
| scaffold | This is scaffolding to build intuition, not a learnable unit | "力场做功解释只是理解曲线积分的一种物理视角" |

## Resulting KP Structure

After consolidation, produce the final KP list:

| kp_id | final_knowledge_item | source_origin | consolidation_note |
|------|---------------------|---------------|-------------------|
| kp-001 | (best retained KP) | su-001 | retained |
| kp-002 | (expanded KP) | su-001 | merged from kp-005 (scatter) |

## Rules

- Every required source content must still be covered after consolidation. Merging does not mean deleting — the content of merged KPs must appear in the parent KP's quick_absorption interpretation section.
- A merged KP's checkpoint question is eliminated; its reading requirement is absorbed into the parent KP's reading task.
- If merging would cause a KP to exceed 8 minutes of estimated reading time, consider splitting instead.

## Minimum Completion Standard

This file fails if:
- Fewer than 3 MCQ_failure_reason codes were considered during evaluation
- Required source content is lost after consolidation (not absorbed into parent KP)
- The post-consolidation KP list omits any required source unit coverage
