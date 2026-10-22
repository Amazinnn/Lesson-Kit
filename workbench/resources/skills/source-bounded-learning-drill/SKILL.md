---
name: source-bounded-learning-drill
description: >-
  Generate source-bounded Lesson Kit practice from PPT, PDF, lecture notes, textbook excerpts,
  or other assigned study material. Use when the task is to turn bounded source material into a
  learning-oriented question bank, checkpoint drill, or exam-oriented practice set. The source is
  the knowledge boundary: every answer must be verifiable from the supplied material. Generated
  Lesson Kit questions are strictly objective-only: yes/no or single-choice. Read TERMINOLOGY.md
  before generating questions and preserve its frozen terms and boundaries.
---

# Source-bounded Learning Drill

Generate **材料约束型随堂练习** from a bounded source while preserving source order, knowledge boundaries, and learning value.

Read `TERMINOLOGY.md` first. Treat it as the single source of truth for the frozen vocabulary and conceptual model. This file defines the executable workflow and acceptance gates.

This authority is local to this Skill's question-design workflow. Lesson Kit's OpenSpec, DATA_MODEL, FILE_CONTRACT and GLOSSARY retain their respective product-contract responsibilities. This Skill restricts its own generated output; it does not retire other response formats supported by Lesson Kit or migrate existing questions.

## Non-negotiable output contract

### 1. Generated questions are objective-only

Every generated Lesson Kit question MUST be automatically gradable and MUST use exactly one of these response formats:

- `quiz_type: "yes_no"` — 判断题
- `quiz_type: "single_choice"` — 单选题

Do **not** generate:

- free-response explanation questions;
- short-answer questions;
- fill-in-the-blank questions;
- proof questions requiring a written proof;
- design questions requiring a written construction;
- calculation questions requiring a typed numeric result;
- code-writing questions requiring free-form code;
- essay or discussion questions;
- any other prompt whose correctness depends on evaluating unconstrained student text.

This restriction is a property of this Skill, not a default that may be silently relaxed.

### 2. Cognitive Operation is not response format

`Locate / Recall`, `Contrast`, `Organize / Induce`, `Explain`, `Reconstruct / Derive`, `Infer`, `Generalize`, and `Boundary / Counterexample` describe **what mental operation the learner performs**. They do not authorize open-ended answers.

Wrap every cognitive operation in an objective response format. Examples:

- Explain → choose the correct explanation.
- Reconstruct / Derive → choose the correct missing step, intermediate value, or derivation sequence.
- Calculation → choose the correct result or the correct calculation path.
- Design → choose the valid instruction sequence / construction among alternatives.
- Boundary / Counterexample → choose the condition or counterexample that actually breaks the claim.

Never turn a semantic `problem_type` such as `explanation`, `calculation`, or `design` into a free-response question.

### 3. Lesson Kit objective payload

When writing a Lesson Kit authored `content-bundle`, use the existing objective-quiz contract rather than inventing a second question-type system.

For `single_choice`:

- provide exactly 4 options;
- all options must be strings, unique, mutually exclusive, and on the same conceptual dimension;
- exactly one option is correct;
- `answer_key` MUST equal the complete text of that option;
- distractors should represent plausible mistakes or misconceptions, not random nonsense.

For `yes_no`:

- `answer_key` MUST be exactly `是` or `否`;
- do not disguise a multiple-claim ambiguous statement as a judgment question;
- the statement must have one defensible truth value under the source scope.

For every graded objective item:

- provide non-empty `error_reason`;
- preserve `source_evidence` precise enough for a reviewer to verify the answer;
- keep `solution` as the compact answer explanation / reasoning, not as a request for free-form response;
- keep semantic `problem_type` separate from `quiz_type`.

When targeting Lesson Kit's current `micro_quiz` persistence contract, emit exactly one knowledge-point reference in `kp_ids` (a one-element list) for each objective question. If planning identifies several relevant knowledge points, choose the dominant tested knowledge point for persistence rather than emitting an invalid multi-KP micro item.

## Inputs

Required:

- one or more bounded study sources;
- target source range or chapter;
- learning mode if supplied by the user.

Optional:

- learner state: `首次学习`, `学过但不熟`, or `复习`;
- time budget;
- existing Lesson Kit knowledge points to reuse;
- existing question pool to avoid duplication;
- requested output container such as authored bundle or practice-set selection.

Do not ask again for learner state when Lesson Kit context already provides reliable evidence.

## Workflow

### Step 1 — Lock the source boundary

Identify the exact PPT/PDF/textbook sections in scope.

Do not use outside facts to make a question answerable unless the user explicitly expands the source boundary. Background knowledge may help you understand the source, but it must not become hidden evidence for the answer.

### Step 2 — Walk the source in reading order

Process the material in its native reading order unless the user explicitly requests another order.

For each local region:

1. identify Source Fragments;
2. map them to existing Knowledge Points when possible;
3. form local Study Blocks without merging distant occurrences merely because they share a Knowledge Point.

### Step 3 — Extract Atomic Claims

Extract facts, definitions, relations, conditions, derivation steps, examples, figures, code behavior, boundary cases, and source-specific distinctions that can support retrieval or reasoning.

Do not turn page count into question count.

### Step 4 — Determine Coverage Obligations

Use Weighted Coverage to decide which Atomic Claims deserve retrieval pressure.

Prioritize:

- core concepts and relations;
- conditions and exceptions;
- easily confused distinctions;
- source-specific derivation steps;
- facts that are easy to skip during reading;
- figure/table/code information that cannot be recovered from generic domain knowledge;
- exam-relevant details when the learning mode is 应试;
- higher-order in-source reasoning when the learning mode is 深入学习.

### Step 5 — Choose Cognitive Operations

Select operations that add Coverage Gain rather than repeating the same recall prompt.

For 应试, strengthen details, conditions, confusion pairs, typical derivations, and testable relations.

For 深入学习, increase `Reconstruct / Derive`, `Infer`, `Generalize`, and `Boundary / Counterexample` while remaining fully source-bounded.

### Step 6 — Convert every candidate to an objective item

Before drafting final wording, decide whether the candidate is better as:

- a judgment statement (`yes_no`), or
- a four-option single-choice item (`single_choice`).

If the concept seems to require an open response, redesign the item rather than emitting an open question.

Typical conversions:

- ask for the correct result among four computed values;
- ask for the correct instruction sequence among four sequences;
- ask which derivation step is valid;
- ask which explanation matches the source;
- ask whether a precise statement is true;
- ask which boundary condition invalidates a claim.

### Step 7 — Design distractors from real errors

For each single-choice question, derive distractors from plausible learner errors:

- sign or unit mistakes;
- confused terms;
- swapped operands or register roles;
- off-by-one / offset mistakes;
- wrong extension or interpretation;
- using a nearby but inapplicable rule;
- reversing a causal relation;
- overgeneralizing beyond a stated condition.

Avoid joke options, obviously impossible values, and options that differ only cosmetically.

### Step 8 — Attach evidence and knowledge mapping

Every question must have evidence sufficient to verify the answer from the source.

Evidence may point to a page, paragraph, figure, table, formula, code block, or example.

For Lesson Kit authored content, reuse canonical Knowledge Point IDs when they exist. Do not invent canonical IDs. Bundle-local keys are allowed only through the governed content-bundle route that later assigns canonical IDs.

### Step 9 — Apply anti-drift guards

Use the quantitative guards in `TERMINOLOGY.md` only to detect obvious under-generation, over-generation, repetition, or imbalance.

Stop when additional questions no longer add meaningful Coverage Gain.

Do not pad the bank to reach a round number.

### Step 10 — Validate before delivery

Run the acceptance gates below on the complete set, not just a sample.

## Acceptance gates

A generated bank is invalid if any gate fails.

### Source gate

- Every answer and rationale is verifiable from Source scope.
- No external fact is required to distinguish the correct option.
- Evidence is present and points to the relevant material.
- Source order is preserved when order is part of the task.

### Objective-format gate

- Open-ended question count is exactly **0**.
- Every question has `quiz_type` equal to `yes_no` or `single_choice`.
- Every `single_choice` has exactly 4 unique options.
- Every `single_choice.answer_key` exactly matches one option.
- Every `yes_no.answer_key` is exactly `是` or `否`.
- Every graded item has a non-empty `error_reason`.
- No question asks the learner to type a derivation, proof, explanation, number, code fragment, or essay as the graded response.

### Pedagogy gate

- Each retained question contributes meaningful Coverage Gain.
- Distractors encode plausible misconceptions or errors.
- High-order Cognitive Operations remain high-order even though the response format is objective.
- The set does not collapse into shallow definition recall merely to satisfy objective formatting.

### Lesson Kit contract gate

When emitting Lesson Kit authored content:

- do not invent canonical `problem_id` or `kp_id` values;
- use the governed content-bundle route for new entities;
- objective items follow the existing `micro_quiz` field contract;
- each persisted objective item maps to exactly one Knowledge Point under the current contract;
- semantic `problem_type` remains independent from objective `quiz_type`;
- selections reference local problem keys before canonical ingest rather than inventing canonical problem IDs.

## Output expectations

When producing a bank, preserve enough structure for review:

- source section / evidence;
- local or canonical Knowledge Point mapping;
- cognitive operation;
- `quiz_type`;
- question stem;
- options when single-choice;
- answer key;
- concise solution / rationale;
- error reason.

Do not expose internal planning prose unless the user asks for it. The deliverable is the validated objective bank or its governed Lesson Kit artifact.
