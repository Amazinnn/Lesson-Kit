# First-Pass Lesson Rendering

Render a source-guided first-pass lesson from the required V17 Stage 1 harness spine.

## Required Inputs

```text
intermediate/first_pass/01_inputs/source-scope.md
intermediate/first_pass/02_analysis/knowledge-points.md
intermediate/first_pass/03_plans/first-pass-structure-plan.md
intermediate/first_pass/04_checks/coverage-check.md
```

Do not render from private reasoning. Do not render if the full knowledge-point inventory is missing.

## Rendering Rules

- Final filename: `（科目名） （第X章） （章名） 速览.md`.
- Preserve `kp_id` exactly in intermediate files and audit mappings only; do not display `kp_id` in the student-facing final artifact.
- Do not display source locations, `knowledge_type`, `writing_view`, `rendering_intent`, `question_target`, answer-block metadata, template labels, or other internal fields in the final artifact.
- Preserve ordinary source order unless `source-scope.md` allows local dependency adjustment or implementation-chain ordering.
- Render each required knowledge point from `quick_absorption` in `first-pass-structure-plan.md`: output the clean definition/formula statement, the brief interpretation sentence (core insight), and the through-line accent sentence. The interpretation must reveal the operational logic, not paraphrase the definition. The final prose may lightly polish but must not expand into a mini-lesson or standalone summary.
- Place checkpoint questions beside the relevant knowledge point; group answers under `#### 本小节答案` at the end of each source section.
- Use single-choice or true/false checkpoint questions by default, with short judgment only when needed.
- Do not ask for calculation, proof, code writing, or real operation in Stage 1 checkpoint questions.
- Checkpoint questions must require returning to the corresponding source section; they must not be answerable from the short statement alone.
- Keep answer explanations short, normally one sentence.
- Keep short explanations to 1-3 sentences and normally under 120 Chinese characters unless the item is formula-, algorithm-, or implementation-heavy.
- Do not add required content that is not registered in `knowledge-points.md`.
- Do not create learning sessions, time boxes, progress logs, completion cards, exam-prep guides, drill sheets, answer routines, or workflow scaffold sections.
- Do not render stage interface fields such as `confusion_export`, `fragile_items`, `deferred_extension_items`, or `candidate_lesson_upgrade_items` into the student-facing final artifact. Preserve those only in intermediate files for later development.
- Through-line accent: For each knowledge point, the `quick_absorption` through-line sentence must choose an angle that recurs across the chapter (identified in `knowledge-relationship-analysis.md`). Do not write standalone explanations. The through-line serves as a breadcrumb that later knowledge points will pick up.
- Scene-judgment MCQ: Each MCQ must require the student to return to a specific source passage (formula, condition, example) to determine the correct answer. The `quick_absorption` interpretation must NOT contain the answer. Test the question: if a student can answer it from the `quick_absorption` alone, the question is too easy and must be redesigned.
- Style prohibition: The final artifact must not contain workflow terminology (首读, 回看, 不要急着, 记住, etc.). The language must be direct and concise — '一针见血'. Each knowledge block must read like a standalone knowledge organization, not a reading instruction sheet.
- Chapter overview (### 本章脉络): Must use a concise list format — one line per section, with section number, section name, and 1-2 keywords. Do not write as a paragraph or prose overview. Example:
  
  ### 本章脉络
  10-1 第二类曲线积分：定义、参数化、格林公式
  10-2 第二类曲面积分：有向曲面、投影、高斯公式
  10-3 斯托克斯公式：空间曲线积分与路径无关
- MCQ format: Each MCQ must have the question stem on its own line, followed by four option lines (A. / B. / C. / D.) each on their own line. Do not write stem and options on the same line or in paragraph form. Example:
  
  Q1. 回看本节定义，dx,dy 在第二类曲线积分中更接近哪一类量？
  A. 平面面积微元
  B. 有向曲线上的坐标增量
  C. 曲线弧长的微分
  D. 被积函数的自变量

## Minimum Completion Standard

This skill fails if it produces a chapter summary, mini-lesson, problem set, answer key, formalistic template, exam-prep guide, drill sheet, answer routine, or timed learning-session plan.

It also fails if the final artifact displays internal fields, old scaffold modules, source locations, or `kp_id`.

This skill also fails if the final artifact contains workflow terminology (首读, 回看, 先确认, 不要急着) or reads like a one-sentence summary rather than a definition + through-line accent.
