# Style Rules

## File Naming

All final subject artifacts must use this filename pattern:

```text
（科目名） （第X章） （章名） （文件功能名）.md
```

Examples:

```text
离散数学 第9章 关系 教案.md
离散数学 第9章 关系 习题集.md
离散数学 第9章 关系 习题集答案.md
离散数学 第9章 关系 速览.md
微积分 第8章 多元函数微分学 速览.md
数据结构 第9章 图算法 速览.md
数字逻辑 第4章 时序电路 速览.md
```

Use the same pattern for later artifacts such as 做题反馈, 反馈诊断, 知识细查, 基础训练, 综合训练, 变式练, or 考前复习包.

## Global Markdown

- Start with the artifact title.
- Do not include generic teaching metadata unless requested.
- Use one `#` title.
- In ordinary chapter notes and first-pass lessons use `###` for major modules and `####` for source sections. Avoid routine body `##` headings and avoid levels deeper than `####`.
- Use bold lead sentences for local definitions, conditions, formulas, warnings, or compact reminders instead of creating micro-headings.
- Use unordered lists for short parallel items.
- Use tables for concise comparison; do not put long prose in table cells.
- Use Mermaid only for classification, process, dependency, state transition, timeline, or workflow.
- Keep visual density near or below one visual block per 600 Chinese characters.
- Preserve source exercise numbering when working from textbook exercises.
- Use `$...$` for inline LaTeX and `$$...$$` only for long, central, or multi-step formulas.
- Never use `\(...\)` or `\[...\]` in Markdown artifacts.

## Source-Guided First-Pass Lessons

A first-pass lesson is a source-reading interface with controlled teaching support. It is not a formal lesson note, not a chapter summary, not a problem set, not an exam-prep guide, and not a timed learning-session plan.

Final Markdown structure:

```text
# （科目名） （第X章） （章名） 速览

### 源材料第 1 节标题
（复杂小节可加一句以内导语，简单小节直接进入知识点。）

**知识点标题**
短说明或阅读引导。必要时补一句边界、条件、前后承接或类比提示。公式组、步骤组、并列条件可使用最多 2-3 条项目符号。

Q1. 轻量检查问题，要求学生回到源材料判断。

#### 本小节答案
Q1：答案。一句话说明判断依据。

### 源材料第 2 节标题
...
```

Do not include workflow scaffolding modules such as 使用说明, 来源与范围, 本章学习形态, 源材料结构, 知识点检查问题, 首读后回忆单, or 后续阶段接口 in the final student-facing first-pass lesson.

Rules:

- `#` is only the file title.
- `###` is a main module.
- `####` is a source section. A section is the smallest source-order unit unless an implementation chain is required.
- Do not use deeper headings. Use knowledge-point cards, lists, and bold labels inside sections.
- The artifact must preserve source order for ordinary chapters. Local dependency adjustment is allowed only when stated in `source-scope.md`. Lab/project artifacts may use implementation-chain ordering when required.
- Every final knowledge point must trace back to `knowledge-points.md` through `first-pass-structure-plan.md`; do not display `kp_id` in the student-facing final artifact.
- The artifact must not explain enough to replace the source.
- The artifact should use natural source-reading prose: short orientation, source-order cues, boundary reminders, and light checkpoint questions that send the student back to the source.
- Add a one-sentence section orientation only when a source section is complex; simple sections should enter the first knowledge point directly.
- Use short natural paragraphs by default. Bullet lists are allowed only for formula groups, step groups, or parallel conditions, and should normally stay within 2-3 bullets.
- Use `#### 本小节答案` as the fixed answer heading at the end of each source section.
- Use single-choice or true/false checkpoint questions by default, with short judgment only when needed.
- Do not ask for calculation, proof, code writing, or real operation in Stage 1 checkpoint questions.
- Checkpoint questions should require returning to the corresponding source section; they should not be answerable from the short statement alone and should not resemble exam questions or textbook exercises.
- Avoid formalistic or exam-prep style. Do not organize first-pass sections as templates, exam-point summaries, answer routines, scoring rubrics, drill sheets, or test-taking strategies.
- Do not create a learning-session layer, 30-60 minute card, progress log, or time-boxed route.

## First-Pass Knowledge Point Rendering

Final student-facing first-pass sections should render knowledge directly and naturally. Do not show internal tracking fields.

Student-facing shape:

```text
**知识点标题**
quick_absorption：公式/定义的干净陈述 + 一句贯穿视角（偏颇切入）。必要时补一句边界、条件、前后承接或类比提示。

Q1. 轻量检查问题，要求学生回到源材料判断。
```

Internal-only fields such as `kp_id`, `knowledge_type`, `source_position`, `writing_view`, `rendering_intent`, `question_target`, and answer-block grouping stay in `knowledge-points.md` and `first-pass-structure-plan.md`.

Short explanation limits (quick_absorption pattern):

- The short explanation follows the quick_absorption pattern: a clean statement of the formula or definition, optionally followed by one "biased" line that provides a through-line perspective.
- The short explanation must be 1-3 sentences.
- The short explanation must not exceed 120 Chinese characters unless the source item is formula-, algorithm-, or implementation-heavy.
- Every knowledge point must list application conditions when the item has conditions, prerequisites, input assumptions, valid scenarios, invalid scenarios, or boundary cases.
- Every knowledge point must include multi-angle interpretation when useful: definition view, operational view, visual view, algorithmic view, implementation view, proof/condition view, or error-boundary view.
- Do not add source-external expansion as required content. If an auxiliary angle is used only for understanding, mark it as auxiliary and keep it short.
- The quick_absorption field is the sole rendering vehicle for student-facing knowledge presentation; do not add workflow-style explanations around it.

## Workflow Terminology Prohibition

The final student-facing artifact must not contain any workflow terminology. Specifically prohibited terms include but are not limited to: 首读, 回看, 不要急着计算, 先确认, 记住, 这里的阅读重点是, or any phrase that addresses the student as a reader of a workflow rather than a reader of knowledge. The artifact must read like a standalone knowledge organization, not a reading instruction sheet.

## Direct Language Style (一针见血)

Knowledge presentation must be direct and concise. Each sentence should carry information — avoid padding. Use declarative statements for definitions and formulas. For through-line accents, choose one angle and state it without hedging. 

- Do: '格林公式将闭曲线积分转为区域二重积分：∮Pdx+Qdy = ∬(Q_x-P_y)dσ'
- Don't: '这里读的不是沿曲线累加长度，而是沿有向曲线累加坐标增量'

The difference: the 'Do' version lets the formula speak for itself; the 'Don't' version explains what the student should think.

## Lessons

A lesson note is a knowledge artifact, not a problem collection.

It should include definitions, meanings, why concepts are introduced, priority, dependency, conditions, boundaries, representation changes, process traces, formulas, model applicability, and sparse functional examples.

It should not include large embedded exercise collections, source exercise IDs as structure, wrong-answer-note sections, invented easy-mistake lists, flat problem-type routines, or end quick-reference tables used as a substitute for a strong body.

Preserve textbook chapter and section order, but reorganize locally for clarity. Preserve minimum-granularity knowledge units while grouping related details into compact sentences or short paragraphs.

## Problem Sets

A problem set is the main training artifact. Problems must map to lesson-note knowledge points and may train concept recognition, operation process, condition use, representation conversion, neighboring-type distinction, transfer under changed conditions, or integrated reasoning.

Keep answers out of the problem set. Preserve original source wording when making textbook-based sets. Add exact handwriting space only when requested or when using a printable exercise command.

## Answer Keys

An answer key should mirror problem numbering and explain key judgments, knowledge calls, main steps, and important boundary conditions. It should not only give final answers.
