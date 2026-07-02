# Skill: KP Consolidation Analysis

Evaluate each knowledge point for scene-judgment MCQ viability and consolidate KPs that cannot support independent scene-judgment questions.

## Required Inputs

```text
intermediate/first_pass/02_analysis/knowledge-points.md
intermediate/first_pass/02_analysis/knowledge-relationship-analysis.md
```

## Required Output

Write `intermediate/first_pass/02_analysis/kp-consolidation-analysis.md`.

## Analysis Rules

### 1. Evaluate Each KP

For each required KP, determine if it can support a meaningful scene-judgment MCQ:

- **Scene-judgment viable**: The KP describes something with application boundaries (when to use this vs that), comparative features, or condition-dependent behavior that can be tested without revealing the answer in quick_absorption.
- **Not viable**: The KP is a definition, term, single condition, or rote fact that cannot be turned into a scene-judgment question without being trivially answerable from the quick_absorption.

### 2. Use All Failure Reason Codes

Apply the full set of 8 MCQ_failure_reason codes from the template. Do not default to a single reason — consider each KP against all relevant codes.

### 3. Apply Merge Rules

Follow the merge_candidate selection rules in the template. Document the rationale explicitly.

### 4. Verify Coverage

After consolidation, verify that all required source content is still represented. Merged content must appear in the parent KP's quick_absorption interpretation section.

## Completion Standard

This skill fails if:
- The consolidation analysis lacks a systematic viability assessment per KP
- Required source content is lost (not absorbed into parent KP)
- The merge rationale is vague or generic
