# ADR 0008: Problem Candidates and Learner Signals

## Status

Superseded (2026-08-30, remove-candidate-store): the candidate store itself is
physically removed; learner signals remain core. See docs/GLOSSARY.md
「候选题 / Problem Candidate」.

## Context

Many useful learning materials contain no ready-made exercises. Lesson-Kit
therefore needs source-grounded question generation, but generated questions
must not silently acquire the same trust as textbook or exam problems. Requiring
the learner to review every generated item before practice would turn practice
into an authoring workflow and would not provide a meaningful quality audit.

The Focus Map also needs durable learner feedback. Its first MVP accepted a
signal-map JSON file, which is useful for handoff but cannot act as the current
state for formal and candidate practice together.

## Decision

Store candidate problems, candidate attempts, and current learner signals in
separate tables inside the existing course SQLite pool.

A candidate starts in `draft`. It becomes `gate_passed` only when both of these
independent checks pass:

- a script-owned structural check validates IDs, enums, KP links, interaction
  shape, source evidence, and readable Markdown blocks;
- an agent-authored semantic audit reports PASS for source grounding, answer
  correctness, training usefulness, and option plausibility.

Learners may practice `gate_passed` candidates without reviewing or approving
them. Import is explicit and also requires both PASS records. Import renders
candidate structure into the unchanged durable `problems` contract and marks
the candidate `imported`.

Candidate origin uses `source_problem`, `adapted_problem`, or
`generated_grounded`. This is separate from the existing `source_kind`, which
continues to describe textbook, quiz, midterm, final, makeup, or other source
categories. Ungrounded free-form generation and exam simulation are outside
the MVP.

Candidate and formal wrong/stuck attempts update `learner_signals`. Signals are
current state rather than an event log: the first evidence is medium, repeated
evidence becomes high, and mastery does not clear it automatically. Signals
may target a knowledge node or an audited relation. Focus Map reads these rows
by default; signal-map JSON remains an explicit compatibility input.

## Consequences

The official problem pool keeps a simple, stable schema and generated content
has a visible trust boundary. Candidate practice remains useful before import,
and its final state can be summarized into durable progress when import occurs.

The course database gains three tables and a migration responsibility. Rich
candidate provenance is intentionally not queryable from the durable problem
row after import; it remains available through the linked candidate row.

Signals do not disappear automatically, so stale high-priority signals require
an explicit future review or resolution action. That behavior is conservative
and keeps the MVP from inferring mastery from a single successful attempt.
