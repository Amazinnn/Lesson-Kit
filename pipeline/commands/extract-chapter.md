# Command: Extract Chapter (抽取章节)

## 一句话定位

从源材料（PDF/PPT/Markdown）抽取知识资产，灌入 lesson-kit 的 SQLite 知识池。Agent 走严谨的 9 步流程，Python 脚本处理机械操作。

## Entry Conditions (何时使用)

**使用此 Command 当：**
- 课程和章节已有源材料（教材 PDF/PPT/Markdown），需要首次灌库
- 需要重新抽取某章（覆盖已有数据）
- 需要为新课程、新章节初始化 SQLite 池子

**不要使用此 Command 当：**
- 章节池子已存在且只需要渲染视图 → 使用对应视图的 Command（如 `views/first-pass/command.md`）
- 只修改少量 KP → 使用未来的 Update/Delete Command（待设计）
- 需要从纯非教材材料（课外书）抽取 → 暂未支持，先手工录入

## Prerequisites

- 源材料文件路径已知（Markdown / PDF / PPT）
- 课程缩写（course）确定（如 `dld`、`ds`、`os`）
- 章节标识（chapter）确定（如 `ch02`）
- 数据库路径已规划（默认 `pool/{course}.db`，整本教材一个库）

## Required Load List

Agent 在执行前必须加载：

1. `pipeline/templates/pool-insert-manifest.md`（manifest JSON schema）
2. `pipeline/skills/pool-field-inference/SKILL.md`（importance/difficulty/fragile 推断规则）
3. V17 提取 skill 按步骤从 `pipeline/skills/` 加载（见 9 步表）
4. `RED_LINES.md`、`STYLE.md`、`FILE_CONTRACT.md`（lesson-kit 全局约束）
5. `docs/design/kp-pool-modular-views.md`（SQLite schema 总览）

## 9 步工作流

| 步 | 层 | Actor | 动作 | 加载 skill | 产出 |
|----|-----|-------|------|-----------|------|
| 1 | — | Script | `create-tables.py --db pool/{course}.db [--force]` | — | SQLite 4 表 + 6 索引 |
| 2 | 01 | Agent | 锁定源范围 | source-and-scope, source-material-type-detection, source-section-indexing | `intermediate/{course}/extraction/{chapter}/01_inputs/source-scope.md` |
| 3 | 02 | Agent | 构建 KP 清单 | first-pass-learning-item-extraction, knowledge-inventory, course-learning-type-detection, type-specific-learning-item-fields, learning-item-granularity, subject-data-structures, subject-math-physics, subject-required-content, learning-evidence-integration | `02_analysis/knowledge-points.md` |
| 4 | 02 | Agent | 关系分析 + KP 合并 | knowledge-relationship-analysis, kp-consolidation-analysis | `02_analysis/knowledge-relationship-analysis.md` + `kp-consolidation-analysis.md` |
| 5 | 03 | Agent | 生成速览结构计划 | checkpoint-question-generation | `03_plans/structure-plan.md` |
| 6 | 02 | Agent | 生成 pool-insert-manifest.json（桥接） | **pool-field-inference** | `02_analysis/pool-insert-manifest.json` |
| 7 | — | Script | `insert-knowledge-points.py --db ... --manifest ... [--upsert]` | — | KP 入 SQLite |
| 8 | — | Script | （跳过 — 章节伴生题不入池） | — | — |
| 9 | — | Script + Agent | `validate-pool.py --db ... --chapter {chapter} [--json]` 生成报告；ERROR 项必须修复后重跑 7 | — | `04_checks/pool-validation-report.md` |

> 步骤 8 故意跳过——`pool-insert-manifest.json` 只承载 KP。场景判断 MCQ 由视图层在渲染时按 `scene-judgment-mcq` skill 临时生成，不入池。

### 步骤 6 是关键桥接

Agent 将 V17 风格的 `knowledge-points.md`（14 列）翻译为符合 SQLite schema 的 JSON manifest。这是 Agent 智能和 Python 机械操作的分界线：

- V17 字段 → SQLite 列映射：详见 `pool-field-inference` skill
- 三个 SQLite 独有字段（importance/difficulty/fragile）在这一步推断填入
- 输出格式严格遵循 `pool-insert-manifest.md` 模板

## Blockers（流程阻塞条件）

- 步骤 2：如果 source-scope.md 标记 BLOCKING gap，**全流程中止**——不可声称 full coverage
- 步骤 7：`insert-knowledge-points.py` 报告 ERROR → 修复 manifest 后重跑
- 步骤 9：`validate-pool.py` exit code = 2（任何 ERROR-level gate 失败）→ **流程未完成**，必须修复

## Output File Checklist

完成后必须存在：

```
pool/{course}.db                                    ← SQLite 库
intermediate/{course}/extraction/{chapter}/01_inputs/source-scope.md
intermediate/{course}/extraction/{chapter}/02_analysis/knowledge-points.md
intermediate/{course}/extraction/{chapter}/02_analysis/knowledge-relationship-analysis.md
intermediate/{course}/extraction/{chapter}/02_analysis/kp-consolidation-analysis.md
intermediate/{course}/extraction/{chapter}/02_analysis/pool-insert-manifest.json
intermediate/{course}/extraction/{chapter}/03_plans/structure-plan.md
intermediate/{course}/extraction/{chapter}/04_checks/pool-validation-report.md
```

## 关键约束

1. **不审但留底**：所有中间文件全量落地，不在生成时审阅。质量控制依赖 SQLite 池子的结构约束（CHECK + gate 验证）。
2. **信得过**：默认走完全自动。发现问题后再用 Update 修。
3. **题不入池**：场景判断 MCQ 是视图层职责，**不要** 把题目写进 manifest 或 DB。
4. **单库多章**：整本教材一个 DB，跨章靠 `kp_id` 前缀（`dld-ch02-...` / `dld-ch04-...`）。SQLite 用 `WHERE kp_id LIKE 'dld-ch02-%'` 过滤。
5. **Agent 即执行者**：此 Command 不需要写新代码。Claude 加载后按步骤执行 → 调 Python 脚本 → 审查报告 → 修复。

## 验证：端到端可工作

完成后能用以下命令验证：

```bash
# 1. 库存在且 schema 正确
sqlite3 pool/{course}.db ".schema"

# 2. KP 行数合理（应该有 ≥10 个核心 KP）
sqlite3 pool/{course}.db "SELECT COUNT(*) FROM knowledge_points WHERE kp_id LIKE '{course}-{chapter}-%'"

# 3. 难度分布、importance 分布正常
sqlite3 pool/{course}.db "SELECT importance, COUNT(*) FROM knowledge_points WHERE kp_id LIKE '{course}-{chapter}-%' GROUP BY importance"

# 4. query-pool.py 能正常查询
python pool/scripts/query-pool.py --db pool/{course}.db --chapter {course}-{chapter} --view first-pass

# 5. validate-pool.py 全部 PASS
python pipeline/scripts/validate-pool.py --db pool/{course}.db --chapter {chapter} --course {course}
# 期望：Result: PASS, errors: 0
```

## 与 V17 skill 的关系

V17 是 lesson-kit 的方法论试验田——`skills/` 目录下的提取 skill 已经在 V17 中打磨。Pipeline 不直接调 V17，而是**复制**到 `pipeline/skills/` 独立维护。这样：

- V17 继续作为方法论迭代用
- pipeline 的 skill 不被 V17 的工作流变动影响
- 两条独立演进路径

## 后续（不阻塞 MVP）

- Update / Delete Command：CRUD 后两件
- `exercises-manifest.json` + `textbook_exercises` 表：课后习题池
- `exam-manifest.json` + `exam_questions` 表：历年卷题目池
- 中间文件自动清理策略：成功入库后旧中间文件归档