# Gate: Problem Source Consistency Gate

For textbook-based problem sets, verify that source numbering, wording, figures/tables, data, subquestions, and section placement are preserved unless the user explicitly requested adaptation.

Do not claim source fidelity when exercises were inferred from memory or text extraction without visual verification.

For selected exercises that depend on figures, pass only if the final problem set is self-contained through a faithful Mermaid redraw, compact textual reconstruction, or explicit unresolved-figure note. Fail if a necessary figure is omitted, treated as decorative without visual checking, or replaced by invented content.

| Failure | Return to | Forbidden repair |
|---|---|---|
| Source wording/numbering/data not verified | `intermediate/lesson_loop/01_inputs/exercise-inventory.md` or `intermediate/lesson_loop/01_inputs/full-exercise-bank.md` | Editing final problem text from memory |
| Figure-dependent exercise is not self-contained | `intermediate/lesson_loop/02_analysis/exercise-knowledge-model-map.md` and `intermediate/lesson_loop/03_plans/selected-and-added-problem-list.md` | Dropping the figure silently or inventing a substitute |
| Visual verification missing | `intermediate/lesson_loop/01_inputs/pdf-reading-log.md` | Citing OCR/text extraction as enough |
