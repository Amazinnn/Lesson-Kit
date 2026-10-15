# Lesson Kit 题目设计术语表 v2

> 用途：作为 `source-bounded-learning-drill` Skill 的术语与设计规则单一真源。  
> 规则：除非现有体系确实无法表达新的设计概念，否则不新增术语、不为已有概念另造同义词。
> 范围：仅约束本 Skill 的出题设计；不覆盖 Lesson Kit 的 OpenSpec、DATA_MODEL、FILE_CONTRACT 或 GLOSSARY，不改变既有题目、产品可用题型或持久字段。

## 1. 顶层出题模式

### Problem-oriented

围绕知识点寻找、整理或生成值得长期练习的成题。

### Learning-oriented

围绕具体学习材料与学习过程组织随堂练习，用连续的检索压力促进阅读、理解和巩固。

### Source-bounded Learning Drill

中文固定表述：**材料约束型随堂练习**。

指 Learning-oriented 模式下，以指定学习材料为知识边界生成的练习。核心约束：

> 删掉指定材料之后，这道题就不应该还能被可靠地产生；重新把材料给一个陌生人，他应该能够仅凭该材料验证答案。

题目的知识闭包必须落在指定材料范围内。

---

## 2. 内容组织

### Knowledge Point

中文固定表述：**知识点**。

长期稳定的语义节点。它描述“学的是什么”，不直接承担具体材料页码或阅读窗口的职责。

一个 Knowledge Point 可以在同一份材料的多个相距很远的位置重复出现。

### Source Fragment

中文固定表述：**材料片段**。

某个知识点在具体学习材料中的一次局部出现，例如：

- PPT 某几页；
- PDF 某一段；
- 某一张图；
- 某一个例题区域；
- 某个代码片段。

同一个 Knowledge Point 可以对应多个 Source Fragment。

### Study Block

中文固定表述：**学习块**。

一次实际阅读和出题所使用的局部材料范围。

Study Block 同时受两类边界约束：

- Knowledge Point 的语义边界；
- Source Fragment 的局部材料边界。

划分时优先取更小、更局部的范围，但必须保留完整的认知动作。

不允许因为一个 Knowledge Point 跨越很多页，就把这些远距离页面强行合并成一个 Study Block。

---

## 3. 题目范围

### Source scope

中文固定表述：**材料范围**。

当前题目允许依赖的具体材料范围。

### KP scope

中文固定表述：**知识点范围**。

当前题目实际涉及的知识点集合。

规划阶段可以识别多个相关 Knowledge Point；但当题目写入 Lesson Kit 当前 `micro_quiz` 客观题契约时，持久化的 `kp_ids` 必须只包含 **1 个主考知识点**。

这是一条输出适配约束，不意味着复杂题不能调动多个概念。

### Question scope

中文固定表述：**题目范围**。

当前题目实际考察的内容边界。

Question scope 必须同时落在 Source scope 与 KP scope 的约束内。

### Evidence

中文固定表述：**证据**。

材料中能够支持答案或推理过程的具体位置。

Evidence 可以落到：

- 页；
- 段；
- 图；
- 表；
- 公式；
- 代码；
- 例子。

Evidence 必须足以让陌生 reviewer 仅凭材料验证正确答案和关键推理。

---

## 4. Cognitive Operation

中文固定表述：**认知操作**。

认知操作描述题目要求学习者“如何处理材料中的信息”。

**Cognitive Operation 不等同于题型，也不等同于作答形式。**

当前固定为以下八类：

### Locate / Recall

定位或回忆材料中的定义、事实、条件、符号含义等。

### Contrast

比较两个或多个概念、公式、方法、条件之间的异同。

### Organize / Induce

整理若干事实并归纳出结构、分类或规律。

### Explain

理解某个结论、步骤、设计或关系为什么成立或有什么意义。

在本 Skill 中，Explain 必须被包装为客观题，例如“选择正确解释”，不能要求学生自由书写解释。

### Reconstruct / Derive

根据材料已有内容补全被省略的推理、计算或推导过程。

在本 Skill 中，可通过选择正确中间步骤、结果、顺序或推导链进行考察，不得要求自由输入完整推导。

### Infer

根据材料中明确给出的信息推出材料逻辑上蕴含、但未直接写出的结论。

### Generalize

在材料已有逻辑范围内改变条件，并判断结论如何推广或变化。

### Boundary / Counterexample

判断结论的适用边界、失效条件或能够否定过度推广的反例。

其中 Infer、Generalize、Boundary / Counterexample 必须严格遵守材料约束，不得偷偷引入外部知识。

---

## 5. Objective Response Format

中文固定表述：**客观作答形式**。

它描述学习者最终如何作答，与 Cognitive Operation、`problem_type` 分离。

`source-bounded-learning-drill` 当前只允许两种客观作答形式：

### Judgment / yes_no

Lesson Kit 字段：`quiz_type: "yes_no"`。

- 题干必须是一个具有明确真值的陈述；
- `answer_key` 只能是 `是` 或 `否`；
- 不允许把多个可分别真假判断的断言硬塞进一个模糊判断题；
- 若提供 options，只能是系统默认的 `是` / `否` 对；通常无需显式提供。

### Single Choice / single_choice

Lesson Kit 字段：`quiz_type: "single_choice"`。

- 固定 **4 个**选项；
- 4 个选项必须唯一；
- 选项应处于同一概念维度；
- 选项必须互斥；
- 只能有一个正确答案；
- `answer_key` 必须等于正确选项的完整文本；
- 干扰项应来自真实误解、计算错误、混淆关系或错误边界，而不是随机错误内容。

### 当前禁止的作答形式

本 Skill 不生成：

- 开放解释题；
- 简答题；
- 填空题；
- 自由输入计算题；
- 自由书写证明题；
- 自由书写设计题；
- 自由代码题；
- 论述题；
- 多选题；
- 任何依赖对自由文本进行语义判分的题目。

“客观题”在当前 Skill 中不是泛称；其允许集合被明确冻结为：

`{ yes_no, single_choice }`

除非 Lesson Kit 的正式产品契约与本 Skill 同步修改，否则不得自行扩大集合。

---

## 6. Semantic problem_type

`problem_type` 描述题目的知识/能力性质，例如 `calculation`、`explanation`、`design` 等。

它不是 response format。

因此允许：

- `problem_type: "calculation"` + `quiz_type: "single_choice"`；
- `problem_type: "design"` + `quiz_type: "single_choice"`；
- `problem_type: "explanation"` + `quiz_type: "yes_no"` 或 `single_choice`。

不允许因为 `problem_type` 是 explanation/design/calculation 就生成自由作答题。

---

## 7. 学习模式

### 浅了解

目标是建立材料的结构感与核心印象。

优先覆盖核心概念和主要关系。

### 常规学习

目标是在合理时间内获得较完整的理解与记忆。

作为没有特殊说明时的默认中间强度。

### 应试

目标是降低考试中的知识遗漏。

除核心内容外，还应加强：

- 细节；
- 条件；
- 易混淆项；
- 典型推导；
- 可考关系。

客观题形式不意味着只出浅层记忆题。应把计算、推导、边界辨析等包装成高质量客观题。

### 深入学习

目标是真正理解材料内部的逻辑，并能够在材料允许的范围内迁移。

提高 Reconstruct / Derive、Infer、Generalize、Boundary / Counterexample 的比例。

即使处于深入学习模式，仍然必须遵守 `{ yes_no, single_choice }` 的客观作答约束。

---

## 8. 学习者状态

当前只保留以下三种表述：

- **首次学习**；
- **学过但不熟**；
- **复习**。

如果 Lesson Kit 已经能够从历史表现可靠判断，则不应重复询问学习者。

---

## 9. 题量与覆盖

### Atomic Claim

中文固定表述：**原子信息**。

材料中能够独立成为一次检索或推理对象的最小信息单位。

题量与覆盖判断从 Atomic Claim 出发，而不是简单从页数出发。

### Weighted Coverage

中文固定表述：**加权覆盖**。

不同 Atomic Claim 的教学价值并不相同。判断哪些内容值得被题目覆盖时，需要考虑其重要性、关系性、推导性、边界性和材料依赖程度。

Weighted Coverage 是判断思想，不要求计算精确总分。

### instructional load

中文固定表述：**教学负载**。

表示一个 Study Block 中可被有效考察的信息量、关系复杂度和理解负担。

教学负载只用于判断 Study Block 的相对轻重，以及帮助防止题量明显漂移。

不使用精确公式计算 instructional load。

可参考：

- 独立事实或定义数量；
- 概念之间的关系数量；
- 可重建的推导链；
- 边界条件、例外和易混淆点；
- 必须阅读图、表、代码或例子才能获得的信息。

### Mode Coverage Ratio

中文固定表述：**模式覆盖率**。

表示不同学习模式对材料覆盖完整度的要求，但不规定固定百分比。

原则上：

- 浅了解：只覆盖理解材料结构所需的核心内容；
- 常规学习：覆盖主要内容和主要关系；
- 应试：覆盖核心内容、细节、条件、易混淆项和典型推导；
- 深入学习：覆盖核心内容，并显著增加解释、推导、推断、推广和边界考察。

### Coverage Obligation

中文固定表述：**覆盖义务**。

一个 Study Block 中值得通过题目产生检索压力的具体学习目标。

题目数量不是预先指定的配置，而是 Coverage Obligation 的结果。

### Coverage Gain

中文固定表述：**覆盖增量**。

新增一道候选题相对于当前题组所带来的尚未覆盖的信息价值。

判断原则：

- 没有新增知识覆盖、认知操作或易错点暴露：删除；
- 只有很弱新增价值：通常删除，应试或深入学习中可酌情保留；
- 有明确新增价值：保留。

### 时间预算

学习者愿意投入到当前学习任务中的总时间。

时间预算约束整个题组，而不是简单规定每页或每个 Study Block 的题目数量。

### 定量夹具

中文固定表述：**定量夹具**。

用于防止题量、重复度、认知操作结构或总练习时长明显漂移的宽松边界。

当前建议边界：

| 学习模式 | 单个 Study Block 通常题量 | 极端上限 |
|---|---:|---:|
| 浅了解 | 0–2 | 3 |
| 常规学习 | 1–3 | 4 |
| 应试 | 2–5 | 6 |
| 深入学习 | 2–5 | 7 |

这些数字是防漂移夹具，不是生成目标。

同一个 Knowledge Point 在同一个 Study Block 中的重复考察通常限制为：

- 浅了解：不超过 1 次；
- 常规学习：不超过 2 次；
- 应试 / 深入学习：不超过 3 次。

只有后续题目采用明显不同的 Cognitive Operation 并产生新的 Coverage Gain 时，才允许继续考察。

### 边际收益停止

当继续新增题目几乎不再产生新的 Coverage Gain 时，停止生成。

---

## 10. 当前生成关系

当前固定使用：

`Question ← (Study Block, KP scope, Cognitive Operation, Objective Response Format)`

整个随堂练习的基本流程：

`材料 → Atomic Claim → Weighted Coverage → Coverage Obligation → Cognitive Operation → Objective Response Format → 题目`

学习模式决定覆盖标准；时间预算、定量夹具和边际收益停止约束题组规模与结构。

不通过精确公式计算唯一题数。

---

## 11. 已确定的设计原则

1. **知识点负责语义组织，材料分块负责学习时的局部性。**
2. **不要让知识图谱决定阅读窗口，也不要让页码污染知识图谱。**
3. 同一个 Knowledge Point 在材料中的重复出现不应自动去重。
4. 同一个 Knowledge Point 可以对应多个 Source Fragment 和多个 Study Block。
5. Study Block 应尽量局部，但必须保留完整的认知动作。
6. 题目的答案与推理必须能够由 Source scope 内的材料验证。
7. 题量不是人工指定值，而是 Coverage Obligation 的派生结果。
8. 新增一道题必须产生新的 Coverage Gain。
9. 定量规则只作为防漂移夹具，不负责计算唯一正确的题目数量。
10. 学习者决定学习模式与时间预算；Skill 决定具体题量与题组构成。
11. 深入学习不等于简单增加题数，而是提高高阶 Cognitive Operation 的比例。
12. **高阶 Cognitive Operation 不得被误写成开放题。**
13. **本 Skill 生成的所有题必须使用 Objective Response Format。**
14. **当前 Objective Response Format 仅允许 `yes_no` 与 `single_choice`。**
15. `problem_type` 与 `quiz_type` 必须分离理解。
16. 后续讨论除非出现新的设计灵感，否则不得为上述概念新增同义术语。

---

## 12. 术语冻结规则

后续默认：

- 不重新命名已有术语；
- 不为已有概念增加同义词；
- 不把普通描述性短语升级成新术语；
- 若现有术语足以表达新设计，必须复用现有术语；
- 只有在现有体系确实无法表达新的设计概念时，才允许提出新术语；
- 新术语一旦被接受，应立即补入本文件；
- 若 Lesson Kit 的正式数据契约变化导致本文件中的输出约束过时，必须在生成新题库前同步更新本文件和 `SKILL.md`，不得只改其中一处。
