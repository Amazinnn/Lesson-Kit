# ADR 0016: Diagnose Bridge Operation

## Status

Accepted.

## Context

Open-ended work (proofs, circuit designs, derivations) exposed two failures of
the original explain-only bridge: self-assessment against a reference design is
"copying the answer" when the learner lacks skill, and a multi-step derivation
that fails at one step has no vocabulary for "here, at this step, I am stuck".
Both need the learner's own work in the task context.

## Decision

Add a second bridge operation, `diagnose`, alongside `explain` (ADR 0012):

- Task context SHALL include `user_answer` (the learner's own text: proof,
  design, derivation) and any step-stuck marking (ADR 0019).
- Teacher conduct variant: **locate before explain** — identify the specific
  error or stuck point first; give a next-step hint, never the full solution;
  end with a comprehension question.
- Output contract sections: `[定位]` (location) → `[提示]` (hint, partial) →
  `[溯源]` (pool knowledge points + source location) → `[追问]` (follow-up
  question). Contract validation applies exactly as for explain.
- Learner answer text is captured through a new `answer_text` column on
  `problem_attempts` (append-only), fed automatically into the diagnose
  context.

## Consequences

"Copying the answer" becomes structurally impossible for the learner who asks
for diagnosis: the contract forbids full solutions in the hint section. Stuck
steps gain a vocabulary and reach the teacher. The bridge stays one protocol
with two operations and two output contracts.
