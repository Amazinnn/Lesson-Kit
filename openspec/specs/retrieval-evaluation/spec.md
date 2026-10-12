# retrieval-evaluation Specification

## Purpose

Defines a developer-only deterministic diagnostic for measuring whether existing read-only data interfaces can retrieve facts required by Agent workflows. It adds no student-facing retrieval behavior.

## Requirements

### Requirement: Evaluate declared retrieval scenarios

The module command `python -m workbench.experiments.retrieval <workspace> --input <manifest.json>` SHALL read a registered workspace and a UTF-8 JSON manifest with a `scenarios` array (which may be empty). It SHALL support `search` scenarios with `entity` (`kp`, `problem`, or `relation`), a non-empty `query`, and non-empty `expected_ids`; `compare` scenarios with an optional `entity` defaulting to `kp`, non-empty `left_query` and `right_query`, and non-empty `expected_ids`; and `kp_history` scenarios with `kp_id` and the complete expected `expected_problem_text`. Invalid scenarios SHALL fail with a diagnostic rather than being guessed or skipped.

For `search` and `compare`, IDs SHALL match exact returned IDs; repeated expected IDs count once. For `kp_history`, matching SHALL be case-insensitive full-text equality. A matching history row SHALL include non-empty problem text and at least one concrete learner outcome: a recognized attempt status (`new`, `answered`, `wrong`, `stuck`, `reviewing`, or `mastered`), nonblank `answer_text` or `note`, a numeric rating from 1 through 5, or a Boolean verdict (including `false` and its SQLite `0`/`1` representation). Timestamps alone, blank text, and unrecognized statuses SHALL NOT count as learner outcomes.

The JSON report SHALL include one result per scenario with its name, kind, pass state, expected and found counts, recall, primitive-read count, and detail. The summary SHALL report scenario, passed, failed, recall, and primitive-read totals. Recall is matched expected facts divided by distinct expected facts; an empty scenario list reports recall `1.0`, and an individual scenario cannot have an empty expected set.

#### Scenario: Exact historical problem text

- **WHEN** a history row has text `P10` and a scenario expects `P1`
- **THEN** the row does not satisfy the expected fact

#### Scenario: Require recorded learner outcome

- **WHEN** a history row contains problem text and only a timestamp, blank text, or an unrecognized status
- **THEN** it does not count as learner evidence

#### Scenario: Preserve false verdict evidence

- **WHEN** a history row contains a Boolean false verdict and readable problem text
- **THEN** it counts as learner evidence

#### Scenario: Current evidence query closes the retrieval gap

- **WHEN** the current three-scenario fixture runs against the existing data primitives, including the bounded knowledge-point evidence query
- **THEN** it reports 3 of 3 scenarios passed, recall `1.0`, and 4 primitive reads

### Requirement: Keep the diagnostic read-only and local

The evaluator SHALL use existing Data read interfaces, SHALL NOT write workspace or learner state, SHALL NOT invoke an LLM or provider, SHALL NOT change product retrieval ordering, and SHALL NOT integrate with the student UI. It SHALL refuse a missing or non-file workspace database before opening a SQLite connection and SHALL leave that path absent or unchanged.

#### Scenario: Missing workspace database

- **WHEN** the registered workspace database path is absent or is not a regular file
- **THEN** evaluation fails before connecting and does not create or alter that path

#### Scenario: Existing workspace database

- **WHEN** a valid registered workspace is evaluated
- **THEN** all database contents remain unchanged
