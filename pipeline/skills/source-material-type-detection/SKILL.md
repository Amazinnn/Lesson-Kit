# Skill: Source Material Type Detection

Classify the source before extracting learning items.

## Required Output

Write `intermediate/first_pass/01_inputs/source-material-inventory.md`.

## Detect

- source kind: textbook PDF, scanned PDF, PPT/PPTX, lab guide, problem sheet, mixed source;
- main carriers: prose, formulas, diagrams, tables, code, pseudocode, circuit diagrams, state diagrams, waveforms, experiment steps;
- completeness risk: complete textbook, compressed slides, scan uncertainty, missing teacher explanation, missing figures, mixed chapter scope;
- required reading policy: PDF visual verification, PPT/PPTX visual-only, figure-dependent reading, code/pseudocode reading.

## Hard Rules

- Do not start learning-item extraction until material type is recorded.
- PPT/PPTX always triggers visual-only reading. Scripts, OCR, XML unpacking, copied text, and speaker notes are forbidden.
- If the source is compressed or incomplete, mark it. Do not silently fill missing explanation from general knowledge.
