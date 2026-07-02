# Source Material Inventory — Discrete Math Ch.6

## Source kind
Textbook PDF (English) → Markdown via MinerU `extract --model pipeline` (no VLM hallucination).

## Main carriers
- **Prose**: long explanatory paragraphs introducing each concept
- **Formulas**: LaTeX-style inline math (`$n_1 \cdot n_2$`) and display math (`$$...$$`)
- **Examples**: marked `EXAMPLE n` with solutions
- **Theorems/Corollaries**: marked `THEOREM n` and `COROLLARY n`
- **Diagrams**: 1 figure referenced (IPv4 addresses), `images/` directory has the extracted raster
- **Tables**: rare, none significant in this chapter
- **Exercises**: present at end of each section, not in scope for this MVP

## Completeness risk
- MinerU pipeline model: **no hallucination**
- OCR errors observed in the source (e.g., "diferent" instead of "different", "Coeficients" instead of "Coefficients", "ofices" instead of "offices") — these are PDF OCR artefacts, not MinerU's fault
- No figures lost — `images/` directory contains the extracted figure

## Required reading policy
- Prose: full read
- Formulas: render as LaTeX (MinerU produces `$...$` markdown math)
- Examples: extract as KP with knowledge_type=`code-implementation` or `method-modeling`
- Theorems/Corollaries: extract as KP with knowledge_type=`concept-property` or `formula-calculation`

## Special flags
- First real-textbook E2E. The schema and scripts have only been tested on a 10-KP mock. Watch for edge cases (large KP count, formula-heavy KP, long body fields).