# 2026-07-07 Problem Pool Unification

The problem-pool draft was redirected from split `textbook_exercises` /
`exam_questions` tables to one durable `problems` table.

Decisions captured:

- Git commits/tags are the version source of truth; zip packages are handoff artifacts.
- `pool/{course}.db` is the course-level SQLite database.
- Durable problems use `problem_id`, `kp_ids`, `problem_text`, `solution`,
  `problem_type`, and `source_kind`.
- `answer` is not a separate field. Final answers and worked explanations both
  live in `solution`, which may be null.
- Problem-set v1 renders a problem set plus a matching solution file and does
  not generate supplemental problems.
- Extraction-stage Markdown fields must preserve clear block breaks; problem
  subparts are stored as separate paragraphs before insertion.
