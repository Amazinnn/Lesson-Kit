> **Template flexibility:** This is a SUGGESTED structure skeleton. The Agent may deviate with documented justification, but MUST pass all gates in `04_checks/` (common x4 + first-pass x2). All deviations must be recorded in `03_plans/structure-plan.md`.

> **Configuration-driven:** The student's natural language intent (captured in `01_inputs/view-scope.md`) may modify this template. Agent should check the Configuration Confirmation table before rendering.

# （科目名） （第X章） （章名） 速览

## Configuration Overrides

Before rendering, check `01_inputs/view-scope.md` Configuration Confirmation table for these overrides:

### MCQ Inclusion

| Config value | Rendering rule |
|-------------|---------------|
| "yes" | Every KP gets a Q. block after its quick_absorption |
| "no" | Omit all Q. and answer blocks throughout the file |
| "selective" | Only `fragile=1` KPs and confused-state KPs get Q. blocks |

### Depth Override

| Config value | Rendering rule |
|-------------|---------------|
| "standard" | Follow the 1-3 sentence rule per KP |
| "lighter" | 1 sentence per KP, omit through-line sentence unless essential |
| "deeper" | Can use 3 sentences + multi-angle perspective on fragile KPs |

### Section Priority

- If student specifies "重点看第X节" → render that section with full detail (all sentences, all Q. blocks if MCQ=yes)
- Other sections may use lighter treatment (1 sentence, fewer Q. blocks)
- Document priority decisions in `03_plans/structure-plan.md`

---

### 本章脉络

10-1 节名：核心内容概述
10-2 节名：核心内容概述
10-3 节名：核心内容概述

每节一行，列出节号、名称和一两个关键词。不加导语、不写成段落。

### 源材料第 1 节标题

复杂小节可加一句以内导语；简单小节直接进入第一个知识点。

**知识点标题**

公式/定义的干净陈述
一句简要解读（定理/概念的核心操作逻辑）+ 一句贯穿视角阐述（从知识点关系分析中选择全章反复出现的角度切入）

Q1. 场景判断问题，必须查看教材中对应公式/条件/例题的具体表述才能答对。
A. 选项1（易犯错误/干扰项）
B. 选项2（正确项）
C. 选项3（易犯错误/干扰项）
D. 选项4（易犯错误/干扰项）

判断题形式：
Q1. 判断陈述句。
A. 正确
B. 错误

**第二个知识点标题**

定义/公式的干净陈述 + 一句贯穿视角阐述（从知识点关系分析中选择全章反复出现的角度切入，不为解释知识点本身）。保持源材料顺序，不写成总结、模板、考点或题型套路。

公式组、步骤组或并列条件可使用最多 2-3 条项目符号：

- 第一条并列信息。
- 第二条并列信息。

Q2. 轻量检查问题。
A. 选项1
B. 选项2
C. 选项3
D. 选项4

#### 本小节答案

Q1：答案。一句话说明判断依据。

Q2：答案。一句话说明判断依据。

### 源材料第 2 节标题

**知识点标题**

定义/公式的干净陈述 + 一句贯穿视角阐述（从知识点关系分析中选择全章反复出现的角度切入，不为解释知识点本身）。

Q1. 轻量检查问题。

#### 本小节答案

Q1：答案。一句话说明判断依据。

---

## Minimum Completion Standard

- The file must preserve source order unless `view-scope.md` explicitly allows local dependency adjustment or implementation-chain ordering.
- The file must not show `kp_id`, source location, `knowledge_type`, `writing_view`, `rendering_intent`, template labels, or internal field names.
- The file must not contain workflow scaffold modules such as 使用说明, 来源与范围, 本章学习形态, 源材料结构, 知识点检查问题, 首读后回忆单, or 后续阶段接口.
- Add a one-sentence section orientation only when a source section is complex; simple sections should enter the first knowledge point directly.
- Use short natural paragraphs by default. Bullet lists are allowed only for formula groups, step groups, or parallel conditions, and should normally stay within 2-3 bullets.
- Questions stay next to the relevant knowledge point; answers are grouped under the fixed `#### 本小节答案` heading at the end of each source section.
- Checkpoint questions must use single-choice or true/false as the default, with short judgment only when needed.
- Checkpoint questions must not require calculation, proof, code writing, or real operation.
- Checkpoint questions must be scene-judgment type — see `skills/scene-judgment-mcq.md` for the Source-Dependency Self-Check Protocol.
- Checkpoint questions should require returning to the corresponding source section to answer confidently; they should not be answerable from the quick_absorption statement alone and should not resemble exam questions or textbook exercises.
- Answer explanations must stay short, normally one sentence.
- The file must not read like a summary, mini-lesson, problem set, formalistic template, exam-prep guide, answer routine, scoring rubric, drill sheet, or learning-session plan.
- No required source content may appear in the final artifact without registration in the pool and planning in `03_plans/structure-plan.md`.
- The `### 本章脉络` section must use a concise list format (one line per section with section number, name, and 1-2 keywords). Do not write it as a paragraph or prose overview.
- MCQ inclusion follows the Configuration Overrides table: check `01_inputs/view-scope.md` before deciding which KPs get Q. blocks.
