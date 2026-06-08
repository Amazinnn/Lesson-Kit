# lesson-kit 视图层设计

**Date:** 2026-06-08
**Status:** 设计完成 — 速览视图首版。习题集后续。
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）

## 架构：两系统分离

lesson-kit 分为两个独立系统，组织原则不同：

| | Pipeline（抽取管线） | Views（视图构建） |
|------|------|------|
| 职责 | 池子增删改查 | 从池子渲染产出 |
| 组织原则 | 按**功能**集中 | 按**视图类型**分区 |
| 目录 | `pipeline/` | `views/` |
| 设计状态 | 另案设计 | **本文档** |

**核心约束：必须先有池子再渲染。** 抽取管线灌入 SQLite，视图从 SQLite 读取。不存在"向后兼容旧 V17 流程"——池子是唯一数据源。

## V17 关系

V17 退居为**学习方法论文档包**：
- V17 是方法论试验田——Skill 在 V17 中开发验证，验证通过后复制到 lesson-kit
- V17 不介入 lesson-kit 的开发流程
- `.claude/skills/educational-theory/`（27 文件）留在 lesson-kit 作为 Claude 运行时参考

## 目录结构

```
lesson-kit/
├── pool/                          ← SQLite + 操作脚本
│   ├── scripts/
│   │   └── query-pool.py          ← 池子查询脚本
│   └── *.db                       ← 运行时 SQLite 文件
│
├── views/                         ← 视图构建系统
│   ├── common/                    ← 跨视图共享
│   │   ├── skills/
│   │   │   └── pool-query.md      ← Agent 查询 SQLite 指南
│   │   ├── gates/
│   │   │   ├── style-and-tone.md
│   │   │   ├── format-rendering.md
│   │   │   ├── no-summary-substitution.md
│   │   │   └── red-lines.md
│   │   └── templates/
│   │
│   ├── first-pass/                ← 速览视图（首版）
│   │   ├── GUIDE.md
│   │   ├── command.md
│   │   ├── skills/
│   │   │   ├── through-line-selection.md
│   │   │   ├── quick-absorption-writing.md
│   │   │   ├── scene-judgment-mcq.md
│   │   │   └── knowledge-framing.md
│   │   ├── gates/
│   │   │   ├── coverage.md
│   │   │   └── mcq-quality.md
│   │   └── templates/
│   │       ├── lesson-template.md
│   │       ├── structure-plan-template.md
│   │       └── view-scope-template.md
│   │
│   └── problem-set/               ← 习题集视图（后续）
│       └── ...
│
├── intermediate/                  ← 运行时中间文件
│   └── {course}-{ch}/{view-name}/{layer}/
│       └── 例: dld-ch02/first-pass/01_inputs/view-scope.md
│
├── output/                        ← 最终学生面向产出
├── RED_LINES.md                   ← lesson-kit 独立维护
├── STYLE.md
└── FILE_CONTRACT.md
```

## 三层指导文档

沿用 V17 的 Command → Skill/Gate/Template 三层：

| 层级 | 是什么 | 职责 |
|------|--------|------|
| **Command** | 工作流编排者 | 定义完整 4 层流程，决定何时调用哪个 Skill、参照哪个 Template、过哪个 Gate |
| **Skill** | 专项能力模块 | Agent 在某步骤加载，获得该步骤所需的领域知识或操作指南 |
| **Gate** | 质量检查点 | 检查产出是否通过特定标准，通过/不通过 |
| **Template** | 结构骨架 | Agent 参照的结构参考，非强制执行 |

## 速览视图（first-pass）

### GUIDE.md

包含三段：视图定位（一句话定义）、适用场景（何时用/何时不用）、设计原理（教育理论依据：测试效应、认知负荷理论、先行组织者）。

### 10 步工作流

| 步 | 层 | 动作 | 产出 |
|----|-----|------|------|
| 1 | — | 创建 intermediate 目录 | 目录结构 |
| 2 | 01 | 查询 kp_progress → Agent 推荐配置 | — |
| 3 | 01 | 和学生确认需求（自然语言，Agent 推荐默认 + 学生可覆盖） | — |
| 4 | 01 | 写 view-scope.md | `01_inputs/view-scope.md` |
| 5 | 02 | 加载 pool-query skill → 调用 pool/scripts/query-pool.py | `02_analysis/kp-query-result.json` |
| 6 | 02 | 加载 through-line-selection skill → 选定贯穿视角 | `02_analysis/through-line-selection.md` |
| 7 | 03 | 加载 quick-absorption + mcq + knowledge-framing skills → 渲染计划 | `03_plans/structure-plan.md` |
| 8 | 03 | 检查每个 KP 落地（标题/阐释/题目/答案） | 同上 |
| 9 | 04 | 过 6 个门禁（common×4 + first-pass×2） | `04_checks/coverage-check.md` |
| 10 | — | 参照 lesson-template 渲染最终 Markdown | `output/...速览.md` |

### 关键设计决策

**学生交互：** 仅在步骤 2-3（01_inputs 开始）。Agent 查 progress 做推荐，学生用自然语言确认需求。充分确认后不再打断——减少返工。产出后如需追加，仅基于已有上下文轻量扩展，不走完整 4 层。

**配置灵活性：** 不限维度，自然语言。学生可以说"快速扫一遍第 2 章，重点看卡诺图"、也可以说"只要 KP 解释不要 MCQ"。Agent 解析意图决定配置，不预设配置菜单。

**结构灵活度：** Template 提供建议结构，Agent 有充分理由可偏离。04_checks 门禁兜底——偏离后必须通过所有门禁。

**个性化：** 按视图类型决定规则强度。速览对 progress 标记轻（confused KP 加一句提示，不改变整体结构）。习题集对 progress 反应强（过滤/加权选题）。

### Skills（4 个，从 V17 复制后独立维护）

| Skill | 职责 |
|-------|------|
| `through-line-selection.md` | 从 related_kp_ids 关系矩阵推导本章贯穿视角 |
| `quick-absorption-writing.md` | 1-3 句阐释：公式/定义 + 一句贯穿视角。最多 120 字 |
| `scene-judgment-mcq.md` | 场景判断选择题设计：题干 + 4 选项，必须回源才能判断 |
| `knowledge-framing.md` | quick_absorption 的多角度阐释：定义视角/操作视角/视觉视角/边界视角 |

### Gates（6 个）

**Common（4 个）：**
| Gate | 检查内容 |
|------|---------|
| `style-and-tone.md` | 一针见血风格，无工作流术语（首读/回看/先确认…） |
| `format-rendering.md` | Markdown 合规：`$...$` 行内 LaTeX，标题层级 `#`/`###`/`####` |
| `no-summary-substitution.md` | 速览不能替代源材料阅读，检查题必须回源才能答 |
| `red-lines.md` | 7 条核心红线 + 反形式主义/反应试导向 |

**First-pass 专用（2 个）：**
| Gate | 检查内容 |
|------|---------|
| `coverage.md` | KP 全覆盖，无遗漏，source_location 对应 |
| `mcq-quality.md` | 场景判断 MCQ 质量：4 选项有区分度，干扰项基于常见错误 |

### Templates（3 个）

| Template | 用途 |
|----------|------|
| `view-scope-template.md` | 01_inputs 范围确认文件结构。和 V17 source-scope.md 对应：source_unit 表格 + 顺序规则 + 触发特性 + 学生意图段落 + 确认配置段落 |
| `structure-plan-template.md` | 03_plans 渲染计划结构：KP 级渲染决策表（student_visible_title, quick_absorption, question_draft, answer_key, answer_explanation, forbidden_rendering） |
| `lesson-template.md` | 最终 Markdown 骨架：`# 速览` → `### 本章脉络` → `### 第N节` → `**KP标题**` → `Q. MCQ` → `#### 本小节答案` |

## pool/scripts/query-pool.py

### 接口

```bash
python pool/scripts/query-pool.py --db pool/dld-ch02.db --chapter ch02 --view first-pass
```

- `--db`: SQLite 数据库路径
- `--chapter`: 章节标识（对应 kp_id 中的章号）
- `--view`: 视图类型（决定查哪些表、哪些字段）
- 输出：JSON 到 stdout，Agent 重定向到 intermediate 文件

### JSON 结构

```json
{
  "kps": [
    {
      "kp_id": "dld-ch02-kp-001",
      "knowledge_item": "布尔代数基本定理",
      "knowledge_type": "concept-property",
      "importance": "core",
      "difficulty": 2,
      "fragile": 0,
      "learning_action": "区分单变量定理与多变量定理的适用范围",
      "related_kp_ids": ["dld-ch02-kp-002", "dld-ch02-kp-008"],
      "source_location": "Section 2-3, pp. 45-47"
    }
  ],
  "questions": [
    {
      "q_id": "dld-ch02-q-001",
      "question_text": "...",
      "answer_key": "B",
      "answer_explanation": "...",
      "kp_id": "dld-ch02-kp-001",
      "difficulty": 1
    }
  ],
  "progress": {
    "kp_states": {
      "dld-ch02-kp-001": "new",
      "dld-ch02-kp-003": "confused"
    },
    "question_states": {}
  }
}
```

## 习题集视图（problem-set）预览

后续设计，已确定的骨架：

| 层 | 中间文件 |
|----|---------|
| 01 | scope.md |
| 02 | kp-list.json + question-list.json + progress.json |
| 03 | selection-plan.md（选题策略 + 顺序 + 难度分布） |
| 04 | coverage + answer-separation-check |

不同于速览：无 through-line，选题策略替代 quick_absorption，难度分布是核心决策。

## 中间文件路径约定

```
intermediate/{course}-{chapter}/{view-name}/{layer}/
```

- `{course}`: 课程缩写，如 `dld`
- `{chapter}`: 章号，如 `ch02`
- `{view-name}`: 视图名，如 `first-pass`、`problem-set`
- `{layer}`: `01_inputs`、`02_analysis`、`03_plans`、`04_checks`

示例：`intermediate/dld-ch02/first-pass/01_inputs/view-scope.md`

## 红线文件

lesson-kit 根目录下的 `RED_LINES.md`、`STYLE.md`、`FILE_CONTRACT.md` 从 V17 复制，独立维护。V17 版本作为方法论参考保留，lesson-kit 版本是实际执行标准。

## 与 V17 的关键区别

| | V17 | lesson-kit |
|------|-----|-----------|
| 数据来源 | 每次从源材料重新提取 KP | SQLite 池子，查一次 |
| 中间文件 | 4 层，每层多个文件 | 4 层，按视图定制文件清单 |
| through-line | 抽取时选定，存入 KP | 每次视图生成时从关系矩阵推导 |
| quick_absorption | 抽取时写好（structure-plan） | 每次视图生成时 Agent 重写 |
| 个性化 | 无 | 查 progress 表，按学生状态出不同内容 |
| 视图扩展 | 新增视图 = 新 Command + 全套中间件 | 新增视图 = `views/` 下一个新文件夹 |
| V17 角色 | 生产系统 | 方法论试验田 |
