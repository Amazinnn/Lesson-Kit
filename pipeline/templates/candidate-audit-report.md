# Template: Problem Candidate Audit Report

`candidate-audit-report.json` is the semantic half of the candidate gate. The
auditing Agent must inspect source evidence and solve the item; the script owns
the separate structural half.

**Location:** `intermediate/{course}/problem_generation/{chapter}/04_checks/candidate-audit-report.json`

**Consumer:** `pipeline/scripts/gate-candidates.py`

```json
{
  "audits": [
    {
      "candidate_id": "dmath-ch06-cand-001",
      "status": "PASS",
      "checks": {
        "source_grounding": "PASS",
        "answer_correctness": "PASS",
        "training_usefulness": "PASS",
        "option_plausibility": "PASS"
      },
      "summary": "The candidate is grounded in the product rule and has one justified answer."
    }
  ]
}
```

Every check and the top-level status must be `PASS` before the candidate may
be practiced or imported. A failed or malformed audit moves the candidate to
`needs_revision`; it never asks the learner to approve the item.
