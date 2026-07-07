# lesson-kit View Layer Design

**Status:** Current v1 view shape.

## Boundary

Pipeline extracts durable assets into `pool/{course}.db`. Views only query the
pool and render student-facing files. A view must not silently create new pool
assets.

## Current Views

### Knowledge Guide View

The first student-facing view. It renders a readable guide from
`knowledge_points` using `pool/scripts/print-graph.py`.

Historical note: some older files still use `first-pass` or `速览` language.
The canonical product term is knowledge guide view.

### Problem-Set View

Located at `views/problem-set/`.

It renders two files from `problems`:

- Problem set: no solutions, no `kp_id`, no internal fields.
- Solution file: same numbering as the problem set; missing solution text is
  shown as `待补`.

Defaults:

- `source_kind=textbook`.
- Coverage-first selection.
- Preserve source/problem order when coverage allows.
- Do not generate supplemental problems in v1.

## Shared Query Interface

```bash
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view problem-set --source-kind textbook
```

For problem-set views the JSON includes:

```json
{
  "kps": [],
  "questions": [],
  "problems": [],
  "progress": {
    "kp_states": {},
    "question_states": {}
  }
}
```

## Intermediate Path

Views use:

```text
intermediate/{course}-{chapter}/{view-name}/
├── 01_inputs/
├── 02_analysis/
├── 03_plans/
└── 04_checks/
```

Problem ingestion is not a view and uses:

```text
intermediate/{course}/problem_extraction/{chapter}/
```
