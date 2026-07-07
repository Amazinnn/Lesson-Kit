# Template: Problem Insert Manifest

`problem-insert-manifest.json` is the Agent-to-script bridge for durable
problems. The Agent extracts problems and maps them to existing KPs; Python
validates and inserts them into SQLite.

**Location:** `intermediate/{course}/problem_extraction/{chapter}/02_analysis/problem-insert-manifest.json`

**Consumer:** `pipeline/scripts/insert-problems.py`

## Complete Schema

```json
{
  "metadata": {
    "course": "dmath",
    "chapter": "ch06",
    "source_files": ["Discrete Mathematics Chapter 6.md"],
    "full_problem_bank_md": "intermediate/dmath/problem_extraction/ch06/01_inputs/full-problem-bank.md",
    "notes": "Problems are stored as problems. Source location is not part of the v1 schema."
  },
  "problems": [
    {
      "problem_id": "dmath-ch06-prob-001",
      "kp_ids": ["dmath-ch06-kp-001"],
      "problem_text": "How many bit strings of length 8 are there?",
      "solution": "Use the product rule: each position has 2 choices, so the answer is $2^8 = 256$.",
      "problem_type": "calculation",
      "source_kind": "textbook"
    }
  ]
}
```

## Required Fields

### metadata

| Field | Required | Notes |
|---|---|---|
| `course` | yes | Course prefix used in IDs. |
| `chapter` | yes | Chapter ID such as `ch06`. |
| `source_files` | recommended | Source files used during extraction. |
| `full_problem_bank_md` | recommended | Audit file containing the complete extracted problem list. |

### problems[]

| Field | Required | Validation |
|---|---|---|
| `problem_id` | yes | `{course}-{chapter}-prob-{NNN}` |
| `kp_ids` | yes | Non-empty list of existing `kp_id` values. |
| `problem_text` | yes | Markdown + LaTeX problem text. |
| `solution` | no | Final answer, explanation, or worked solution. `null` means not filled yet. |
| `problem_type` | yes | See enum below. |
| `source_kind` | yes | See enum below. |

## Enums

`problem_type`:

```text
calculation | proof | modeling | explanation | experiment |
design | application | counterexample | other
```

`source_kind`:

```text
textbook | quiz | midterm | final | makeup | other
```

## Rules

- Do not add `answer`; final answers belong in `solution`.
- Do not add `training_target`, `condition_axes`, or source-location fields to v1.
- Keep duplicate-looking problems as separate rows when they come from separate source occurrences.
- `kp_ids` is required because problem-set views select by knowledge coverage.
- `solution` may be missing. Problem-set solution files must show missing solution entries as pending.
