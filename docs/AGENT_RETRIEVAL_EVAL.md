# Agent retrieval evaluation

Lesson Kit should improve Agent retrieval from measured failures, not from a guessed RAG architecture. The developer-only diagnostic lives at `workbench.experiments.retrieval`; it calls existing Data read interfaces, computes metrics locally, and never invokes an LLM or provider. It does not change product retrieval ordering or learner state.

Run it against a registered workspace from the repository root:

```text
python -m workbench.experiments.retrieval <workspace> --input <manifest.json>
```

The workspace database must already be a regular file. A missing path or a directory is rejected before SQLite connects, without creating or changing that path. Evaluation leaves existing database contents unchanged.

## Manifest

The UTF-8 JSON file contains a `scenarios` array. The current scenario kinds are:

| Kind | Required fields | Reads |
|---|---|---:|
| `search` | `entity` (`kp`, `problem`, `relation`), non-empty `query`, non-empty `expected_ids` | 1 |
| `compare` | optional `entity` (defaults to `kp`), non-empty `left_query`, `right_query`, and `expected_ids` | 2 |
| `kp_history` | `kp_id`, complete expected `expected_problem_text` | 1 |

For example:

```json
{
  "scenarios": [
    {
      "name": "find a knowledge point",
      "kind": "search",
      "entity": "kp",
      "query": "Pigeonhole Principle",
      "expected_ids": ["dmath-ch07-kp-001"]
    },
    {
      "name": "compare across chapters",
      "kind": "compare",
      "left_query": "Counting",
      "right_query": "Pigeonhole Principle",
      "expected_ids": ["dmath-ch06-kp-001", "dmath-ch07-kp-001"]
    },
    {
      "name": "recover a recorded problem",
      "kind": "kp_history",
      "kp_id": "dmath-ch06-kp-001",
      "expected_problem_text": "The complete problem_text value stored for this attempt"
    }
  ]
}
```

Search and comparison expectations are exact IDs; duplicate expected IDs count once. Historical problem text is matched by case-insensitive full-text equality, so `P1` does not match `P10`. A history row counts only when it has nonblank problem text and a concrete outcome: a recognized attempt status (`new`, `answered`, `wrong`, `stuck`, `reviewing`, `mastered`), nonblank `answer_text` or `note`, a numeric rating from 1 through 5, or a Boolean verdict (including false and SQLite `0`/`1`). Timestamps alone, blank text, and unrecognized statuses are not learner outcomes. The evaluator does not require a private attempt identifier or any one specific outcome field.

Unknown scenario kinds and malformed required fields fail with a diagnostic; they are not skipped or guessed. An empty `scenarios` array is valid and reports zero scenarios, zero reads, and recall `1.0`.

## Report

The command prints a JSON object to stdout with `summary` and `results`. `summary` contains `scenarios`, `passed`, `failed`, `recall`, and `primitive_reads`. Each result contains `name`, `kind`, `passed`, `expected_count`, `found_count`, `recall`, `primitive_reads`, and `detail`. A missing name becomes `scenario-N`. Per-scenario recall is matched expected facts divided by distinct expected facts; total recall uses the same ratio across all scenarios. `passed` means all expected facts for that scenario were found.

`detail` records the inputs relevant to each scenario. Search includes `query` and `entity`; compare includes `left_query`, `right_query`, and `entity`; history includes `kp_id`, the number of rows with concrete learner evidence, and the one-read evidence requirement. `primitive_reads` counts explicit retrieval calls made by the evaluator, not internal SQL statements or runtime cost.

## Historical baseline before the evidence query (PR117, 2026-10-12)

The regression fixture covers three representative questions: find a knowledge point outside the active chapter by name; retrieve two knowledge points for a cross-chapter comparison; and answer “did I previously make this kind of mistake?” from a knowledge-point history read.

After the outcome and full-text checks were corrected, the existing `data history <workspace> kp <id>` primitive produced this validated baseline:

```text
scenarios:       3
passed:          2
failed:          1
recall:          0.75
primitive_reads: 4
```

The first two scenarios pass because exact keyword search already finds knowledge points course-wide. The history scenario fails because the generic history read returns knowledge-point feedback/state/schedule/signals, but not attempted problems together with readable question text. An Agent can reconstruct the answer by reading linked problems and their history, but that adds retrieval calls and opportunities to miss evidence. This is a retrieval-cost and reliability gap, not evidence for semantic search. An earlier 3/3 result from the uncorrected evaluator was a false green: timestamps and substring matches could satisfy the history scenario without retrieving the expected problem and a concrete learner outcome.

## Current synthetic baseline after the evidence query

The fixture now uses the bounded `data.evidence.for_kp` read for its history scenario. It returns the requested problem text with a recorded learner outcome in one primitive read:

```text
scenarios:       3
passed:          3
failed:          0
recall:          1.0
primitive_reads: 4
```

## Decision rule

Do not add vector search, a memory Agent, or another planning layer because a scenario sounds semantic. For each observed miss:

1. reproduce it as a deterministic scenario;
2. distinguish missing facts from excessive fan-out;
3. make the smallest read-only data change that closes the measured gap;
4. rerun the same scenario;
5. only consider heavier retrieval machinery if keyword/data retrieval still misses relevant objects after the cheaper fix.

The first measured target was knowledge-point historical evidence aggregation. The new evidence query closes that gap; no semantic search is indicated by this fixture.
