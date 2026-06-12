# lesson-kit 抽取管线设计（Create）

**Date:** 2026-06-09
**Status:** 设计完成
**依赖:** [kp-pool-modular-views.md](./kp-pool-modular-views.md)（SQLite Schema）

## 定位

抽取管线（Pipeline）和视图构建（Views）是 lesson-kit 的两套独立系统：

| | Pipeline | Views |
|------|------|------|
| 职责 | 池子增删改查 | 从池子渲染学习产出 |
| 方向 | 源材料 → SQLite | SQLite → Markdown |
| 组织原则 | 按功能集中 | 按视图类型分区 |

本文档覆盖 **Create**（抽取 + 入库），是 CRUD 的 C。Update / Delete 后续设计。

## 核心设计决策

### 1. 自动化程度：全自动

- 用户指定课程、章节、源文件路径
- Claude 自动完成全部步骤，不打断、不审阅
- 质量策略："信得过，用的时候再说"——发现问题再 Update / Delete 修

### 2. 提取方式：V17 完整分析流程

Claude 加载 V17 提取 skill（从 lesson-kit/skills/ 复制到 pipeline/skills/ 独立维护），走严谨的 4 层分析流程。

### 3. 中间文件策略

全量落地 `intermediate/`，不审但留底。用于将来追溯和排查。

**新路径结构（一个数据库对应整本教材）：**
```
intermediate/{course}/
├── extraction/{chapter}/    ← Pipeline 中间文件
│   ├── 01_inputs/source-scope.md
│   ├── 02_analysis/knowledge-points.md + knowledge-relationship-analysis.md + kp-consolidation-analysis.md + pool-insert-manifest.json
│   └── 03_plans/
│
├── first-pass/{chapter}/    ← 速览视图中间文件
│   ├── 01_inputs/view-scope.md
│   ├── 02_analysis/kp-query-result.json + through-line-selection.md
│   ├── 03_plans/structure-plan.md
│   └── 04_checks/coverage-check.md
│
└── problem-set/{chapter}/   ← 习题集视图（后续）
```

### 4. 数据库粒度

**一个教材一个数据库**：`pool/dld.db`（数字逻辑设计）、`pool/ds.db`（数据结构）等。

`kp_id` 保持 `{course}-{chapter}-kp-{NNN}` 格式（如 `dld-ch02-kp-001`），一章内过滤用 `WHERE kp_id LIKE 'dld-ch02-%'`。

### 5. Skill 组织

Pipeline skill 从 lesson-kit/skills/ 复制到 pipeline/skills/，独立维护。和 views/first-pass/skills/ 一致——各管各的。

### 6. 池子独有字段推断

importance（core/supplementary/optional）、difficulty（1-5）、fragile（0/1）三个字段 V17 没有，在 V17 提取步骤中直接填。不新建独立 skill——作为 knowledge-points.md 模板的自然扩展。

推断规则（Agent 在步骤 6 遵循）：

| 字段 | 值 | 推断依据 |
|------|-----|---------|
| `importance` | core | 出现在章学习目标/标题中；被 ≥3 个其他 KP 依赖；是大定理/法则/定义性方法 |
| | supplementary | 支撑 core KP；提供上下文/应用例/变体；缺失不阻塞主线 |
| | optional | 扩展内容；标记为"选读"；练习衍生 KP 的 extension_supplement |
| `difficulty` | 1 | 单一定义/术语/符号。纯记忆 |
| | 2 | 定义带条件，单步直接应用 |
| | 3 | 多步过程，多条件交互的公式 |
| | 4 | 跨概念复杂推理，算法状态跟踪 |
| | 5 | 抽象理论，跨域集成，有取舍的设计决策 |
| `fragile` | 1 | 关系分析中有 contrast/analogy 关系；有反直觉行为；已知常见混淆对 |
| | 0 | 边界清晰，无已知常见误解。不确定时默认 0 |

### 7. JSON Manifest 桥接

Agent 产出 JSON manifest → Python 脚本消费灌库。

路径：`intermediate/{course}/extraction/{chapter}/02_analysis/pool-insert-manifest.json`

格式：
```json
{
  "metadata": {
    "course": "dld",
    "chapter": "ch02",
    "source_file": "Logic Computer Design Fundamentals Chapter 2.md",
    "knowledge_points_md": "intermediate/dld/extraction/ch02/02_analysis/knowledge-points.md"
  },
  "knowledge_points": [
    {
      "kp_id": "dld-ch02-kp-001",
      "knowledge_item": "布尔代数基本定理",
      "source_location": "Section 2-3, pp. 45-47",
      "knowledge_type": "concept-property",
      "related_kp_ids": ["dld-ch02-kp-002", "dld-ch02-kp-008"],
      "importance": "core",
      "learning_action": "区分单变量定理与多变量定理的适用范围",
      "difficulty": 2,
      "fragile": 0
    }
  ]
}
```

### 8. 入库脚本

**一个脚本搞定全部**：`pipeline/scripts/populate-pool.py`

```bash
# 建表（4 张表 + 6 个索引）
python pipeline/scripts/populate-pool.py --db pool/dld.db --init

# 灌数据
python pipeline/scripts/populate-pool.py --db pool/dld.db --chapter ch02 --manifest intermediate/dld/extraction/ch02/02_analysis/pool-insert-manifest.json

# 重新灌某章（覆盖）
python pipeline/scripts/populate-pool.py --db pool/dld.db --chapter ch02 --manifest ... --upsert
```

- `--init`：执行 CREATE TABLE（全部 4 张表），如果表已存在则报错
- `--manifest`：读取 JSON manifest，INSERT 到 knowledge_points 表
- `--chapter`：指定章节（记录在 metadata 中，用于验证 kp_id 一致性）
- `--upsert`：INSERT OR REPLACE（修复时用）

### 9. 题目：不进池子

章节伴生选择题（场景判断 MCQ）作为视图附属品，在视图生成时临时产生。不在此 Pipeline 阶段入 questions 表。

**questions 表保留但暂时为空。** 未来用途：课后习题池、历年卷题目池——它们独立设计，不在此次 Create 范围内。

题池拆分方向（记录意图，后续设计）：
- **课后习题池**：原书课后习题，按节对应 KP，存题目 + 答案 + 解析
- **历年卷池**：历年考试真题，按年份 + 题型存储
- **章节伴生题**：不入池，视图生成时临时出

### 10. Pipeline 目录结构

```
pipeline/
├── commands/
│   └── extract-chapter.md       ← 9 步工作流编排
├── skills/                      ← 15 个提取 skill（从 skills/ 复制，独立维护）
│   ├── source-and-scope/SKILL.md
│   ├── source-material-type-detection/SKILL.md
│   ├── source-section-indexing/SKILL.md
│   ├── first-pass-learning-item-extraction/SKILL.md
│   ├── knowledge-inventory/SKILL.md
│   ├── course-learning-type-detection/SKILL.md
│   ├── type-specific-learning-item-fields/SKILL.md
│   ├── kp-consolidation-analysis/SKILL.md
│   ├── knowledge-relationship-analysis/SKILL.md
│   ├── learning-item-granularity/SKILL.md
│   ├── subject-data-structures/SKILL.md
│   ├── subject-math-physics/SKILL.md
│   └── subject-required-content/SKILL.md
└── scripts/
    └── populate-pool.py         ← 建表 + 入库（--init / --manifest / --chapter）
```

Pipeline 不设自己的 gates/（"信得过"）和 templates/（中间文件模板沿用 V17 的 templates/intermediate/）。

## 9 步工作流

| 步 | 层 | 动作 | 产出 |
|----|-----|------|------|
| 1 | — | `populate-pool.py --db pool/dld.db --init` | 4 张空表 + 索引 |
| 2 | 01 | 锁定源范围（加载 source-and-scope + source-material-type-detection + source-section-indexing skill） | `01_inputs/source-scope.md` |
| 3 | 02 | 构建完整 KP 清单（加载 first-pass-learning-item-extraction + knowledge-inventory + course-learning-type-detection + type-specific-learning-item-fields + learning-item-granularity + subject-* skill） | `02_analysis/knowledge-points.md` |
| 4 | 02 | 知识关系分析（加载 knowledge-relationship-analysis skill） | `02_analysis/knowledge-relationship-analysis.md` |
| 5 | 02 | KP 合并分析（加载 kp-consolidation-analysis skill） | `02_analysis/kp-consolidation-analysis.md` |
| 6 | 02 | 推断 importance/difficulty/fragile，为每个 KP 补全池子独有字段 | 更新 `02_analysis/knowledge-points.md` |
| 7 | 02 | 生成 pool-insert-manifest.json（V17 格式 → SQLite 格式桥接） | `02_analysis/pool-insert-manifest.json` |
| 8 | — | `populate-pool.py --db pool/dld.db --chapter ch02 --manifest ...` | KP 入 SQLite |
| 9 | — | 输出统计摘要（Agent 读库生成：KP 总数、core/supplementary/optional 分布、难度分布、fragile 占比） | 终端输出 |

## 统计摘要格式（步骤 9）

```
📦 pool/dld.db — 第 2 章 组合逻辑电路 入库完成

KP 总数: 28
  core:          12 (42.9%)
  supplementary: 13 (46.4%)
  optional:       3 (10.7%)

难度分布:
  1 (记忆):      4 (14.3%)
  2 (直接应用):  10 (35.7%)
  3 (多步过程):  11 (39.3%)
  4 (复杂推理):   3 (10.7%)
  5 (抽象理论):   0 (0.0%)

易错 KP (fragile=1): 5 (17.9%)
  - dld-ch02-kp-008 (卡诺图化简与代数化简的等价性)
  - dld-ch02-kp-015 (Setup time vs Hold time)
  - ...
```

## 与视图层的交互

Pipeline 产出物是填好的 SQLite 数据库（如 `pool/dld.db`）。View 层通过 `pool/scripts/query-pool.py` 消费：

```bash
# 速览视图查询（需要更新 --db 路径为整本教材库 + 加 --chapter 过滤）
python pool/scripts/query-pool.py --db pool/dld.db --chapter dld-ch02 --view first-pass
```

**注意：** query-pool.py 的参数需要更新——`--db` 现在指向整本教材库，`--chapter` 过滤具体章节。

## 后续

- **Pipeline 实现**：目录创建、skill 复制、populate-pool.py 编写、Command 文件编写、端到端测试
- **题池设计**：课后习题池 + 历年卷题目池 schema
- **CRUD 扩展**：Update / Delete（修改已有 KP、删除错误 KP、合并拆分的 KP）
- **query-pool.py 更新**：适配整本教材库（`--db` → `--db` + `--chapter`）
