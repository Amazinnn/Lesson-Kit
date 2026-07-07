# Skill: Problem-Set Rendering

Render selected problems as practice material.

Rules:

- The problem-set file contains problem text only, never solution text.
- The solution file mirrors the selected problem numbers.
- If `solution` is null or empty, write `待补` in the solution file.
- Do not show `kp_id`, `source_kind`, `problem_type`, or other internal fields
  in the student-facing problem set.
- Keep problem statements compact. Do not add explanatory scaffolding unless it
  is part of the stored `problem_text`.
