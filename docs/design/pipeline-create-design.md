# lesson-kit Pipeline Create Design

**Status:** Current v1 create flows.

## Boundary

Pipeline creates durable pool assets. Views render from those assets.

## Course Database

Each course uses one SQLite database:

```text
pool/{course}.db
```

Chapter scope is expressed by ID prefixes such as `dmath-ch06-kp-001` and
`dmath-ch06-prob-001`.

## KP Create Flow

Command: `pipeline/commands/extract-chapter.md`

Main scripts:

```bash
python pipeline/scripts/create-tables.py --db pool/{course}.db
python pipeline/scripts/insert-knowledge-points.py --db pool/{course}.db --manifest <pool-insert-manifest.json>
python pipeline/scripts/validate-pool.py --db pool/{course}.db --course {course} --chapter {chapter}
```

## Problem Create Flow

Command: `pipeline/commands/extract-problems.md`

Main scripts:

```bash
python pipeline/scripts/insert-problems.py --db pool/{course}.db --manifest <problem-insert-manifest.json> --strict
python pipeline/scripts/validate-pool.py --db pool/{course}.db --course {course} --chapter {chapter}
```

Problem extraction is independent from KP extraction. It requires the chapter's
KPs to already exist.

## Problem Manifest Contract

`pipeline/templates/problem-insert-manifest.md` defines the v1 problem fields:

```text
problem_id, kp_ids, problem_text, solution, problem_type, source_kind
```

No `answer` field exists. Answers and explanations both live in `solution`,
which may be null.

## Deferred Work

- Update/delete commands for existing KPs and problems.
- Problem-level progress tables.
- Generated supplemental problems.
