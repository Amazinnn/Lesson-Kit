# Agent retrieval evaluation

Lesson Kit should improve Agent retrieval from measured failures, not from a guessed RAG architecture.

The deterministic evaluator lives at `workbench.experiments.retrieval`. It calls the same read-only content primitives available to the Agent-facing data layer and never invokes an LLM. A manifest describes synthetic questions and the facts that must be recoverable.

Run it against a registered workspace with:

```text
python -m workbench.experiments.retrieval <workspace> --input <manifest.json>
```

## Metrics

Each scenario reports:

- `recall`: required facts found / required facts expected;
- `primitive_reads`: the minimum explicit retrieval calls made by the evaluator;
- `passed`: whether all required facts were recovered;
- scenario detail, including whether historical evidence is understandable without a second id lookup.

The evaluator intentionally does not judge prose quality. It measures whether the data layer can place the necessary evidence in front of an Agent.

## Initial synthetic baseline

The regression fixture covers three representative questions:

1. Find a knowledge point outside the current chapter by name.
2. Retrieve two knowledge points for a cross-chapter comparison.
3. Answer “did I previously make this kind of mistake?” for a knowledge point using recorded problem attempts.

With the current data primitives, the first two scenarios pass. Exact keyword search already finds knowledge points course-wide, so there is no evidence yet that Lesson Kit needs embeddings or a vector database for these cases.

The third scenario fails the single-read evidence criterion. `data history <workspace> kp <id>` returns knowledge-point feedback/state/schedule/signals, but it does not include the attempted problems under that knowledge point together with their readable question text. An Agent can reconstruct the answer by fanning out from the KP to related problems and then reading each problem's history, but that is a retrieval-cost and reliability problem rather than a semantic-search problem.

Fixture baseline:

```text
scenarios:       3
passed:          2
failed:          1
recall:          0.75
primitive_reads: 4
```

## Decision rule

Do not add vector search, a memory Agent, or a second planning layer because a scenario sounds semantic.

For each observed miss:

1. reproduce it as a deterministic scenario;
2. distinguish missing facts from excessive fan-out;
3. make the smallest read-only data change that closes the measured gap;
4. rerun the same scenario;
5. only consider heavier retrieval machinery if keyword/data retrieval still misses relevant objects after the cheaper fix.

The first measured target is therefore **knowledge-point historical evidence aggregation**, not semantic embeddings.
