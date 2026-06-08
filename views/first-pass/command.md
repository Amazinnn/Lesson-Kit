# Command: Create First-Pass View (速览)

## 一句话定位
从 SQLite 知识池渲染章节速览——轻量源材料导航 + 场景判断自检。池子驱动，每次生成重写 through-line 和 quick_absorption。

## Entry Conditions (何时使用)
**使用此 Command 当：**
- 学生首次接触某章节，需要源材料导航
- 学生想要轻量自检（场景判断 MCQ），不需要深度练习
- 章节的 SQLite 池子已由抽取管线创建且不为空

**不要使用此 Command 当：**
- 学生需要深度讲解（→ lesson 视图，未来）
- 学生需要大量练习题（→ problem-set 视图，未来）
- 章节池子不存在或为空（→ 先运行抽取管线）

## Prerequisites
- SQLite 池子存在：`pool/{course}-{ch}.db` 包含 `knowledge_points` 和 `questions` 表
- 学生已指定章节和大致需求（可自然语言）

## Required Load List
Agent 在执行前必须加载以下文件：

RED_LINES.md
STYLE.md
FILE_CONTRACT.md
views/common/skills/pool-query.md
views/first-pass/skills/through-line-selection.md
views/first-pass/skills/quick-absorption-writing.md
views/first-pass/skills/scene-judgment-mcq.md
views/first-pass/skills/knowledge-framing.md
views/common/gates/style-and-tone.md
views/common/gates/format-rendering.md
views/common/gates/no-summary-substitution.md
views/common/gates/red-lines.md
views/first-pass/gates/coverage.md
views/first-pass/gates/mcq-quality.md
views/first-pass/templates/view-scope-template.md
views/first-pass/templates/structure-plan-template.md
views/first-pass/templates/lesson-template.md

## Workflow

### Step 1: Create Intermediate Directory
创建中间文件目录结构：
```
intermediate/{course}-{ch}/first-pass/
├── 01_inputs/
├── 02_analysis/
├── 03_plans/
└── 04_checks/
```
- `{course}`：课程缩写，如 `dld`
- `{ch}`：章号，如 `ch02`
- 如果目录已存在（之前生成过），清理旧中间文件

### Step 2: Query Progress & Recommend Config
**加载 Skill：** `pool-query.md`

查询学生进度：
```bash
python pool/scripts/query-pool.py --db pool/{course}-{ch}.db --chapter {course}-{ch} --view first-pass
```

解析 `progress.kp_states`，汇总学生状态：
- 哪些 KP 是 `confused` 或 `faded`（需要额外关注）
- 哪些 KP 是 `stable`（已掌握，可轻量处理）
- 哪些 KP 是 `new`（首次接触）

Agent 基于进度数据生成推荐配置：
- **scope**：默认 full（全章）。如果 progress 显示某几节大部分 KP 为 `stable`，建议可跳过
- **mcq_inclusion**：默认 yes。如果学生之前已做完本章全部 MCQ，建议 selective（仅 confused KP 出题）
- **depth_override**：默认 standard。如果较多 confused KP，建议 deeper
- **section_priority**：默认 none。如果存在集中 confused 的节，建议优先

### Step 3: Confirm with Student
向学生呈现自然语言的推荐摘要（不是配置表格——用对话口吻）：

> 📖 **第 X 章速览配置建议**
>
> 你之前学过这一章，其中 [X] 个知识点标记为模糊（confused），主要在 [节名] 一节。其余 [Y] 个知识点已稳定掌握。
>
> 我建议：全章过一遍，但对 [节名] 侧重展开，对已稳定的知识点一笔带过，并给模糊的知识点各出一道场景判断题。整份速览大约 [估计篇幅]。
>
> 这样可以吗？或者你有其他想法？（比如「只看模糊的部分」、「不要题目」、「快速扫一遍就行」）

学生用自然语言确认或覆盖。如果学生沉默，Agent 应主动追问。

⚠ **确认前不要进入步骤 4。** 充分的步骤 3 确认是减少返工的关键。

### Step 4: Write view-scope.md
**参照 Template：** `view-scope-template.md`

将步骤 3 确认的结果写入 `01_inputs/view-scope.md`：
- 范围锁定（course/chapter/sections）
- 学生原始需求（自然语言原文）
- Agent 解析意图
- 配置确认表（Agent 推荐 vs 学生确认）
- 勾选 `config_confirmed`

⚠ `config_confirmed` 未勾选 = 文件不完整。不得进入步骤 5。

### Step 5: Query Pool
**加载 Skill：** `pool-query.md`

执行完整查询，保存结果：
```bash
python pool/scripts/query-pool.py --db pool/{course}-{ch}.db --chapter {course}-{ch} --view first-pass \
  > intermediate/{course}-{ch}/first-pass/02_analysis/kp-query-result.json
```

验证 JSON 完整性：
- `kps` 数组非空
- 每个 KP 有 `kp_id`、`knowledge_item`、`knowledge_type`、`importance`
- `questions` 数组可能为空（池子尚无题目）
- `progress` 可能为空（学生尚未开始学习）

如果查询失败（数据库不存在/表缺失/kps 为空），**停止并报告错误**。不得继续。

### Step 6: Select Through-Line
**加载 Skill：** `through-line-selection.md`

分析 `kp-query-result.json` 中的 `related_kp_ids` 关系网络。

选定 1-2 个贯穿视角，写入 `02_analysis/through-line-selection.md`：
- 选定的 through-line 名称和类型
- 覆盖的 KP 数量和比例（需 ≥50%）
- 为什么选这个角度（教学价值/复杂度/风险）
- 应用到每个 KP 的具体连接方式

⚠ 如果某 KP 和选定的 through-line 无明显关联，在文件中标注。Agent 在步骤 7 中仍需尝试连接，连接失败则在 `forbidden_rendering` 中记录。

### Step 7: Write Structure Plan
**加载 Skill：** `quick-absorption-writing.md`、`scene-judgment-mcq.md`、`knowledge-framing.md`
**参照 Template：** `structure-plan-template.md`、`lesson-template.md`

对 `kp-query-result.json` 中的每个 KP，在 `03_plans/structure-plan.md` 中填写：

| 字段 | 说明 |
|------|------|
| `kp_id` | 从池子直接复制 |
| `student_visible_title` | 基于 `knowledge_item` 改写为学生友好的标题 |
| `quick_absorption` | 1-3 句。融入 through-line。脆弱 KP 加边界提示。confused KP 加一句额外提示 |
| `question_target` | 基于 `learning_action` 确定 |
| `question_draft` | 场景判断 MCQ（题干 + A/B/C/D）。如 config 为 no MCQ，此列标 "—" |
| `answer_key` | 单字母。如 config 为 no MCQ，标 "—" |
| `answer_explanation` | 一句话判断依据。如 config 为 no MCQ，标 "—" |
| `answer_block_group` | 答案归属的小节 |
| `forbidden_rendering` | 禁止的呈现方式（内部字段、总结性语言、考试术语等） |

⚠ 遵循配置覆盖规则：
- MCQ=no → 题目相关列标记 "—"，不删除行
- depth=lighter → 每 KP 1 句，跳过 through-line 句
- depth=deeper → 可用 3 句 + 多角度阐释
- section_priority → 优先节全量，其他节 lighter

⚠ 步骤 3 的确认结果映射到此处——Agent 不应在此步骤重新解释学生意图。

### Step 8: Verify KP Landing
检查 `03_plans/structure-plan.md` 中每个 KP：
1. 是否都有 `student_visible_title`（非空、非 `kp_id` 原文）？
2. 是否都有 `quick_absorption`（非空、符合长度限制）？
3. 如果 config 要求 MCQ，是否有 `question_draft`？
4. 如果有 `question_draft`，是否同时有 `answer_key` 和 `answer_explanation`？
5. `forbidden_rendering` 是否列出了该 KP 的特有禁止项？

如果任何 KP 不满足，在步骤 9 之前修复。

### Step 9: Run Gates
运行全部 6 个门禁：

**Common Gates（4 个）：**
- `style-and-tone.md` — 风格和语调
- `format-rendering.md` — Markdown 格式合规
- `no-summary-substitution.md` — 不替代源材料
- `red-lines.md` — 核心红线

**First-Pass Gates（2 个）：**
- `coverage.md` — KP 覆盖和源追溯
- `mcq-quality.md` — 场景判断 MCQ 质量

将门禁结果写入 `04_checks/coverage-check.md`（包含所有 6 个门禁的通过/失败状态）：
- 通过的 gate：记录 "✅ PASS"
- 失败的 gate：记录失败原因 + 返回层级 + 禁止的修复方式

如果任何 gate 失败：
1. 定位最早破损的层级（01/02/03）
2. 回到该层级修复根本原因（不是修补最终 Markdown）
3. 修复后重新运行后续步骤
4. 循环直到所有 gate 通过

⚠ **所有 gate 必须通过才能进入步骤 10。** 不得在 gate 失败时渲染产出。

### Step 10: Render Final Markdown
**参照 Template：** `lesson-template.md`

将 `03_plans/structure-plan.md` 中的渲染计划组装为最终 Markdown。

文件命名遵循 `STYLE.md`：`（科目名） （第X章） （章名） 速览.md`

输出路径：`output/` 或学生指定的输出目录。

⚠ 渲染时检查：
- 内部字段（kp_id、knowledge_type、source_location 等）不出现在最终产物中
- 工作流术语不出现
- `#### 本小节答案` 放在每节末尾
- 章节脉络简洁（每节一行 + 1-2 个关键词）
- 源节顺序保持（除 view-scope.md 中有记录的调整外）

## Blockers
以下情况**停止流程，不得继续**：
- 步骤 3：学生未确认配置
- 步骤 5：池子查询失败（数据库不存在/表缺失/kps 为空）
- 步骤 6：无法选定覆盖 ≥50% KP 的 through-line
- 步骤 9：任何 gate 失败且无法修复
- 任何步骤：中间文件目录创建失败

## Output File Checklist
生成完成后，以下文件应全部存在：

```
intermediate/{course}-{ch}/first-pass/
├── 01_inputs/
│   └── view-scope.md          ← 范围锁定 + 学生意图 + 确认配置
├── 02_analysis/
│   ├── kp-query-result.json   ← 池子查询原始结果
│   └── through-line-selection.md ← 贯穿视角选定
├── 03_plans/
│   └── structure-plan.md      ← KP 级渲染计划
└── 04_checks/
    └── coverage-check.md      ← 门禁结果

output/
└── （科目名） （第X章） （章名） 速览.md ← 最终学生面向产物
```

## Light Extension Protocol
如果学生在拿到速览后请求追加内容（"第 3 节再加详细一点"）：

1. **可以做的事（不走完整 4 层）：**
   - 在 `structure-plan.md` 中追加或修改指定 KP 的 `quick_absorption`
   - 追加新的 MCQ（需通过 `mcq-quality.md` 门禁）
   - 重新渲染最终 Markdown
   - 更新 `coverage-check.md` 记录变更

2. **不可以做的事（需要回到完整流程）：**
   - 更改 through-line（影响全局，需重新走步骤 6-9）
   - 新增 KP（需要重新查询池子和覆盖检查）
   - 更改配置（需要回到步骤 3-4）
   - 更改章节范围（需要回到步骤 2-4）

如果学生请求超出轻量扩展范围，Agent 应说明原因并建议重新走完整流程。
