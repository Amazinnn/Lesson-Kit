# Skill: PPT/PPTX Source Handling

Handle slides as visual sources only.

## Required Output

Write `intermediate/first_pass/01_inputs/ppt-visual-reading-log.md` and trigger `intermediate/first_pass/04_checks/ppt-visual-reading-check.md`.

## P0 Rule

PPT/PPTX sources must be read only through rendered slide images. Scripts, OCR, XML unpacking, copied slide text, speaker-note extraction, and batch text extraction are forbidden.

## What to Read Visually

- visible slide text;
- diagrams, arrows, layout, indentation, emphasis, color, and grouping;
- code snippets and pseudocode layout;
- tables and field relationships;
- formulas and labels;
- figures, state diagrams, circuit diagrams, waveforms.

## Slide-Specific Learning Items

Prefer items based on observable slide objects: fields, process steps, complexity notes, diagrams, warnings, “not work”, “improvement”, “good if”, and examples.

Do not treat slide titles alone as enough learning items.

If a slide appears compressed or missing teacher explanation, mark the missing context. Do not invent a full explanation.
