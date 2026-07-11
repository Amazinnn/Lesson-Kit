# Template: Problem Candidate Insert Manifest

`candidate-insert-manifest.json` is the Agent-to-script bridge for
source-grounded practice candidates.

**Location:** `intermediate/{course}/problem_generation/{chapter}/02_analysis/candidate-insert-manifest.json`

**Consumer:** `pipeline/scripts/insert-candidates.py`

```json
{
  "metadata": {
    "course": "dmath",
    "chapter": "ch06"
  },
  "candidates": [
    {
      "candidate_id": "dmath-ch06-cand-001",
      "kp_ids": ["dmath-ch06-kp-001"],
      "problem_text": "A task has three independent stages.\n\nHow many outcomes are possible?",
      "options": [
        {
          "id": "A",
          "text": "$3$",
          "explanation": "This counts stages, not choices."
        },
        {
          "id": "B",
          "text": "$2^3$",
          "explanation": "Each stage has two choices."
        }
      ],
      "correct_option_id": "B",
      "solution": "The product rule gives $2^3=8$.",
      "problem_type": "calculation",
      "interaction_type": "single_choice",
      "generation_purpose": "first_pass_check",
      "origin_kind": "generated_grounded",
      "source_kind": "textbook",
      "source_evidence": [
        {
          "source": "Discrete Mathematics Chapter 6.md",
          "location": "Section 6.1, product rule",
          "basis": "Independent stage counts multiply."
        }
      ]
    }
  ]
}
```

## Enums

- `interaction_type`: `single_choice | true_false | free_response`
- `generation_purpose`: `first_pass_check | remediation`
- `origin_kind`: `source_problem | adapted_problem | generated_grounded`
- `problem_type`: `calculation | proof | modeling | explanation | experiment | design | application | counterexample | other`
- `source_kind`: `textbook | quiz | midterm | final | makeup | other`

## Rules

- Every candidate links to one or more existing KPs and has non-empty source evidence.
- `solution` contains the answer and explanation; do not add `answer`.
- Choice options require unique IDs, text, and explanations. The correct ID must match one option.
- Every wrong remediation option requires `error_lure` with `signal_type`, `target_type`, and `target_id`.
- `error_lure.signal_type` uses `weak_node`, `confusion`, `missing_prerequisite`, `transfer_failure`, or `relation_gap`.
- `free_response` uses null or absent `options` and `correct_option_id`.
- Keep stems, subparts, formulas, and solution steps in blank-line-separated Markdown blocks.
