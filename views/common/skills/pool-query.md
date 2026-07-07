# Pool Query Skill

## Purpose

Query a course-level SQLite pool for a chapter and return JSON for view
rendering.

## Command

```bash
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view {view-name}
```

For problem-set views, optionally filter by source kind:

```bash
python pool/scripts/query-pool.py --db pool/dmath.db --chapter dmath-ch06 --view problem-set --source-kind textbook
```

Parameters:

- `--db`: course-level SQLite file, e.g. `pool/dmath.db`.
- `--chapter`: full chapter prefix, e.g. `dmath-ch06`.
- `--view`: `knowledge-guide`, `first-pass`, or `problem-set`.
- `--source-kind`: optional problem filter for `problem-set`.

## Output Shape

Base output:

```json
{
  "kps": [],
  "questions": [],
  "progress": {
    "kp_states": {},
    "question_states": {}
  }
}
```

Problem-set output adds:

```json
{
  "problems": [
    {
      "problem_id": "dmath-ch06-prob-001",
      "kp_ids": ["dmath-ch06-kp-001"],
      "problem_text": "Problem text.",
      "solution": null,
      "problem_type": "calculation",
      "source_kind": "textbook"
    }
  ]
}
```

## Agent Rules

- Save the raw JSON in the view's `02_analysis/` layer.
- Treat `questions` as legacy companion-check data.
- Treat `problems` as the durable practice pool.
- Do not show `kp_id`, `problem_id`, `source_kind`, or `problem_type` in
  student-facing problem sets.
- In solution files, `solution = null` renders as `待补`.

## Normal Empty States

- Empty `progress`: normal for a new learner.
- Empty `questions`: normal; companion checks may be view-generated.
- Empty `problems` in a problem-set query: blocker for problem-set rendering.
