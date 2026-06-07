# Skill: First-Pass Learning Item Extraction

Extract knowledge-point reading tasks from the source. These are not lesson headings and not summary bullets.

## Required Output

Write `intermediate/first_pass/02_analysis/candidate-learning-item-inventory.md`.

## Learning Item Definition

A learning item is a concrete knowledge-point task that a student can acquire by returning to a specific source location. A normal item should take about 3–8 minutes.

## Candidate Sources

Extract candidates from:

- definitions, formulas, theorems, conditions, models;
- diagrams, tables, state diagrams, waveforms, matrices, graphs;
- code/pseudocode fields, loops, state variables, complexity notes;
- examples or exercises that reveal a first-pass reading need;
- low-visibility source details that affect later understanding.

## Reject

Reject candidates that are:

- whole-section titles;
- isolated symbols with no independent reading task;
- general themes that cannot be checked;
- AI-invented study advice not grounded in the source;
- full explanations that would replace the source.
