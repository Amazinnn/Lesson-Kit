# Agent retrieval evaluation

Lesson Kit should improve Agent retrieval from measured failures, not from a guessed RAG architecture.

The deterministic evaluator lives at `workbench.experiments.retrieval`. It calls the same read-only primitives available to the Agent-facing data layer and never invokes an LLM. A manifest describes synthetic questions and the facts that must be recoverable.

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

## Synthetic baseline

The regression fixture covers three representative questions:

1. Find a knowledge point outside the current chapter by name.
2. Retrieve two knowledge points for a cross-chapter comparison.
3. Answer “did I previously make this kind of mistake?” for a knowledge point using recorded problem attempts.

Exact keyword search already handles the first two scenarios course-wide, so there is still no evidence that Lesson Kit needs embeddings or a vector database for these cases.

The original third scenario exposed a fan-out gap: `data history <workspace> kp <id>` did not carry the attempted problems under that knowledge point together with readable question text and learner outcomes. The first measured production fix adds a dedicated read-only evidence view:

```text
lesson-kit evidence <workspace> kp <kp-id> [--limit N]
```

It returns a bounded newest-first set of actual attempt evidence with problem text, learner answer/choices when recorded, verdict/status, linked rating/feedback when available, and time. Internal ids remain available for provenance, but the result itself contains the human-readable facts an Agent should cite to the learner.

Current fixture result after that fix:

```text
scenarios:       3
passed:          3
failed:          0
recall:          1.0
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

The next evaluator expansion should target temporal and practice-scoped history questions before any broader retrieval architecture is added.
