# Scene-Judgment MCQ Design

## 一句话定位

MCQ 的价值不在于"测会不会"，而在于暴露学生的错误心智模型。在速览视图中，MCQ 的目标更窄——判断学生能否在具体场景中辨认概念/条件/公式的适用性，即 TRANSFER，而非 recall。

## Scene-Judgment vs. General MCQ

| Dimension | Scene-Judgment MCQ | General MCQ |
|-----------|-------------------|-------------|
| **What it tests** | TRANSFER: Can the student recognize which concept/condition/formula applies in a concrete scenario? | RECALL: Does the student remember a definition? COMPUTE: Can the student arrive at a result? |
| **Stem form** | "某电路需要在三个输入信号中检测是否有且仅有两个为高电平…" — a specific, situated context | "下列哪项是卡诺图的化简规则？" — a direct knowledge check |
| **Answering requires** | Locating a specific passage, figure, table, or formula in the source AND applying judgment | Recalling the definition or performing a calculation |
| **First-pass allowed?** | YES — this is the only allowed question type in first-pass view | NO — belongs in problem-set or lesson-loop views |

**Rule:** In first-pass view, ONLY scene-judgment MCQs are allowed. Calculation, proof, code-writing, and definition-recall questions belong in problem-set view.

## Source-Dependency Self-Check Protocol

Before approving each MCQ, the agent MUST answer three questions:

1. **Source-dependency check:** Can this question be answered by reading only the quick_absorption text? If YES → FAIL. Rewrite so that the student must locate a specific passage, figure, table, or formula in the source material.

2. **Distractor authenticity check:** Does each wrong option represent a real, documented common error for this `knowledge_type`? If NO → FAIL. Research common errors for this type of knowledge. Each distractor must be tempting to a student with a specific misconception.

3. **Source-specificity check:** Does answering correctly require locating a specific passage, figure, table, or formula in the source? If NO → FAIL. Make the question more source-specific — reference page numbers, figure captions, table entries, or formula indices implicitly.

## Question Structure Rules

Every scene-judgment MCQ in first-pass follows this exact structure:

```
Q[N]. [One scenario sentence — a concrete, situated context.]

A. [Option 1 — a real misconception-based distractor]
B. [Option 2 — correct answer]
C. [Option 3 — a real misconception-based distractor]
D. [Option 4 — a real misconception-based distractor]
```

- **Stem:** One scenario sentence on its own line. Sets up a concrete situation that requires judgment.
- **Options:** Exactly 4, labeled A. B. C. D., each on its own line.
- **Distractors:** Homogeneous (all about the same type of judgment), mutually exclusive (only one correct), based on common misconceptions.
- **Answer:** Single letter (A/B/C/D) in the answer section. No explanation inline with options.
- **Answer explanation:** One sentence maximum. States the judgment basis, not a mini-lesson. Pattern: "判断依据：[specific source element], [condition]成立/不成立。"

## Prohibited Question Types in First-Pass

The following question types MUST NOT appear in first-pass view. They belong in other views (problem-set, lesson-loop):

| Prohibited Type | Example (DO NOT USE) | Why Prohibited |
|----------------|---------------------|----------------|
| Definition recall | "Which of the following is the definition of a minterm?" | Tests recall, not scene judgment. Source-dependency check fails. |
| Calculation | "Compute the SOP expression for F(A,B,C) = Σm(1,3,5,7)" | Tests computation skill, not scene judgment. Belongs in problem-set. |
| Proof | "Prove that XOR is associative" | Tests proof construction. Belongs in problem-set or exam-prep. |
| Code writing | "Write Verilog code for a 4-bit adder" | Tests implementation skill. Belongs in lab or problem-set. |
| Exam-style | Any question containing 解题入口/本题考查/得分点/高频考点 language | Violates 反形式主义/反应试导向 design philosophy. |

## Related Theories

- **Testing Effect** (see fundamentals/testing-effect.md): Retrieval practice strengthens memory. Every MCQ is a learning event, not just an assessment.
- **Error-Driven Learning**: The brain learns most from prediction errors. A wrong answer that surprises the student is more instructive than a correct answer that confirms what they already knew.
- **Cognitive Diagnosis**: Different wrong answers reveal different misconceptions. The same question answered incorrectly for different reasons requires different remediation.
- **ICAP Framework** (see fundamentals/icap-framework.md): Answering an MCQ moves the learner from Passive (reading) to Active (selecting), a significant engagement upgrade. Scene-judgment MCQs go further — they require Constructive engagement (applying a rule to a novel scenario).

## Teaching Application

- Each wrong option must reflect a real, common misconception — not a randomly wrong answer.
- Design options so that "I think I get it but I actually don't" students reveal themselves.
- Three option design principles:
  - **Homogeneous**: All options on the same conceptual dimension
  - **Mutually exclusive**: Options don't overlap
  - **Verifiable**: The correct answer can be confirmed from source material
- Before writing options, list 3-4 common student misunderstandings for this concept. Then turn each into a distractor.
- A good MCQ tests whether the student knows why the other options are wrong, not just which one is right.

## Aha Moment

> An option that nobody ever selects is not a distractor — it's filler. A good distractor is tempting enough that some students genuinely choose it. In scene-judgment MCQs, the most informative wrong answer is the one that reveals the student has memorized the definition but cannot apply it.

## In-workflow Application

- `gates/mcq-quality.md`: Gate that enforces the Source-Dependency Self-Check Protocol and prohibits non-scene-judgment question types in first-pass.
- `templates/structure-plan-template.md`: The question_target, question_draft, answer_key, and answer_explanation columns in the KP-Level Rendering Plan.
- `templates/lesson-template.md`: The Q./A. block structure rendered in the final lesson.
- `skills/through-line-selection.md`: Scene-judgment questions should connect to the through-line where possible — the scenario can echo the chapter's recurring pattern.
