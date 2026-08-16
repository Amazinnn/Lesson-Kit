# ADR 0019: Learning Actions Beyond Problems

## Status

Accepted.

## Context

The subject stress-test (discrete math proofs, digital logic designs, college
English vocabulary, Marxist theory essays, physics derivations) showed the
problem-only practice model is too narrow: vocabulary needs cards, proofs need
stuck-step granularity, open-ended work needs the learner's own answer text.
Each is a distinct learning action with its own data needs.

## Decision

Three learning actions extend the problem-session model:

1. **Directional cards for `memory-recall` knowledge points.** A card is
   prompt-front, recall, reveal-back. Cards carry a direction (e.g. English →
   Chinese and Chinese → English); each direction is an independent learning
   action with its own schedule entry. `review_schedule` keys on
   `(item_type, item_id, direction)` with direction defaulting to an empty
   string for undirected items. `contrasts` and `variant_of` neighbors are
   shown during card practice as compare hints — related review, not merged
   items (per ADR 0015's exclusion).
2. **Step-level stuck marking.** Multi-step solutions are presented as blocks;
   the learner can mark "stuck at block N" with an optional note. The marking
   is recorded on the attempt and enters explain/diagnose context (ADR 0016).
   Solution text format is unchanged — block splitting is a display-time
   concern.
3. **Answer text capture.** `problem_attempts` gains an `answer_text` column
   (append-only, additive migration). Open problem types (proof, design,
   modeling, explanation, application) show an answer box; the latest attempt's
   text feeds diagnose tasks.

All three are additive: no existing table contract changes, no fixed session
flow is imposed — each action is offered by the UI, never required.

## Consequences

The tool now covers the memory-recall and open-ended work its subjects
actually demand. Data stays append-only and evidence-pure. The scheduling
engine gains one composite key dimension and one new interaction type; both are
small, testable extensions of the learning-model layer.
