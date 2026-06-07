# Gate: PPT/PPTX Visual Reading Check

This gate is mandatory for PPT/PPTX sources.

| Failure | Return to | Forbidden repair |
|---|---|---|
| PPT/PPTX content was read by script, OCR, XML unpacking, copied text, or speaker notes | `intermediate/first_pass/01_inputs/ppt-visual-reading-log.md` | Claiming the extracted text matches the slide |
| Slide-image reading log missing | `intermediate/first_pass/01_inputs/ppt-visual-reading-log.md` | Adding a slide list after item generation |
| Learning item lacks slide number/visual area | `intermediate/first_pass/02_analysis/candidate-learning-item-inventory.md` | Citing only slide title |
| Diagram/layout/arrows/code indentation ignored | `intermediate/first_pass/01_inputs/ppt-visual-reading-log.md` | Using only visible text bullets |
| Unreadable slide content guessed | `intermediate/first_pass/01_inputs/ppt-visual-reading-log.md` | Filling gaps with general knowledge |

Pass only when all slide-derived claims come from rendered slide image understanding.
