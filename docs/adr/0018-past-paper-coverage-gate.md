# ADR 0018: Past-Paper Coverage Gate

## Status

Accepted.

## Context

Textbooks measured in centimeters do not line up with actual exams. Full
coverage of "all exam points" cannot be trusted to diligence alone ("AI with
patience can always do it") — it needs a machine-checked contract. The
high-SNR input diet (ADR 0013) already prioritizes past papers; this decision
makes their coverage enforceable.

## Decision

- Extraction inputs SHALL include past exam papers (the exam itself is a
  first-class source, not an afterthought).
- A machine-readable coverage contract,
  `01_inputs/past-paper-coverage.json`, SHALL map every exam point to a pool
  knowledge point or durable problem.
- The coverage gate SHALL fail with the list of unmapped exam points when any
  point lacks a mapping. The workbench SHALL surface unmapped exam points as
  pool gaps eligible for the candidate-generation path (ADR 0008), never as
  silently invented content.
- Bridging "textbook → exam" happens through two structural paths: extracted
  real exam problems enter the durable pool (with `source_kind` marking), and
  gaps feed the future `generate` bridge operation whose explicit type-space
  goal is induction, transfer, and generalization variants — the failure mode
  observed with raw AI chat.

## Consequences

Coverage becomes a gate result, not a claim. The learner's pool is guaranteed
to span the exam surface or explicitly say what it is missing. Cost: one new
intermediate contract file and one gate check, both following existing
patterns.
