# ADR 0013: High-SNR Input Diet and Test-First Practice

## Status

Accepted.

## Context

The MIT NotebookLM 48-hour exam case demonstrated a study method that works:
feed only high-signal-to-noise material (syllabus, past exam papers, classic
explanations of core concepts), have AI generate questions rather than
summaries, review backwards from wrong answers, and simulate being challenged.
Direct AI-chat attempts failed the same way in practice here: generated
questions were too easy, mimicked original structure and phrasing, and lacked
induction, transfer, and generalization.

## Decision

Adopt the case's principles structurally, not as prompts:

- **Input diet**: extraction prioritizes high-SNR sources — syllabus, past
  papers, classic explanations of core concepts — over low-value lecture
  transcripts. The pool contract already requires source evidence per item;
  this decision extends that preference to source selection.
- **Test-first**: practice starts from problems, not from reading material.
  Wrong answers drive the next step (reverse review, ADR 0010).
- **Reverse review**: a wrong or stuck result immediately offers re-practice of
  the same knowledge-point group (workbook requirement), which is the
  structural form of "review backwards from wrong answers".
- **Question generation over summarization**: when the pool has gaps, the
  candidate-generation pipeline (ADR 0008) creates source-grounded candidates
  — never summaries — and induction/transfer/generalization variants are an
  explicit future enhancement of that pipeline's question type space.
- Pool shortages are reported, never silently padded with invented content.

## Consequences

The workbench inherits a study loop with demonstrated exam results, translated
into data and rules. Generation quality is improved by architecture (contracts,
gates, evidence) rather than by prompt tweaks — the failure mode observed with
raw AI chat is addressed at the design level.
