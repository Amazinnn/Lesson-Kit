# Skill: Checkpoint Question Generation

Generate concrete Stage 1 checkpoint questions that send the student back to the source.

## Required Output

Support `intermediate/first_pass/03_plans/first-pass-structure-plan.md`, especially these KP-level rendering fields:

```text
question_target
scene_judgment
question_form
question_draft
answer_key
answer_explanation
answer_block_group
```

Do not create a separate final `知识点检查问题` section.

## Requirements

- Every required knowledge point should have one checkpoint question.
- Questions stay beside the relevant knowledge point in the final `速览`.
- Answers are grouped under `#### 本小节答案` at the end of the corresponding source section.
- Use single-choice or true/false by default, with short judgment only when needed. MCQ must have exactly 4 options (A/B/C/D). Wrong options must be common mistakes or plausible distractors — not obviously wrong. Options must be clearly differentiated from each other.
- MCQ type must be scene_judgment by default: the question requires the student to judge which concept/formula/condition applies to a given scenario. Do not ask for definition recall, formula recognition, or trivial true/false on stated facts.
- Scene-judgment MCQ must require the student to reference a specific source passage (formula, condition statement, example) to determine the answer. Test: if the quick_absorption interpretation alone provides enough information to answer correctly, the question fails.
- For KPs consolidated per kp-consolidation-analysis.md, no independent MCQ is needed — the content is absorbed into the parent KP's question.
- Questions must target a concrete source detail: definition condition, formula variable, use condition, algorithm field, diagram relation, code step role, signal, state transition, boundary, or failure condition.
- Questions must require returning to the corresponding source section to answer confidently.
- Questions must not be answerable from the short student-facing statement alone.
- Questions must not resemble exam questions, textbook exercises, drill practice, or answer routines.
- Questions must not require calculation, proof, code writing, or real operation.
- Answers may include only the answer choice / judgment plus one short sentence explaining the decisive source criterion.
- Question stems must be clean — do not embed option information in the stem. All distinguishing information belongs in the options.

## Reject Vague or Mis-scoped Questions

Reject questions such as:

- “Do you understand this section?”
- “What is the main idea?”
- “Why is this important?”
- “Summarize this chapter.”
- Calculation/proof/code-writing prompts.
- Exam-prep prompts such as `本题考查`, `解题入口`, `题型套路`, `得分点`, or similar variants.

## Good Question Forms

- Which set/object/condition does this definition depend on?
- Which field changes in one algorithm round?
- Which signal/state/table cell should be observed?
- Which formula condition would fail here?
- Which next step best matches the source procedure?
- Which statement matches the boundary given in the source section?
- Which formula/concept applies to this scenario?
- Under which condition would this theorem fail?
- Given this problem description, what is the correct approach?
- Which of the following scenarios requires [concept A] rather than [concept B]?
- MCQ options should feel natural: each wrong option represents a real misunderstanding a student might have, not a straw man.
- MCQ format: The question stem must be on its own line, followed by four option lines (A. B. C. D.) each on their own line. Do not write stem and options in a single paragraph.
