# lesson-kit

**模块化学习材料生成器。** 从源材料自动抽取知识资产到 SQLite 池，按需渲染为多样化的学习格式。

核心理念："**不是帮你跳过源材料，是帮你回到源材料。**"

## 两系统架构

```
源材料（PDF/PPT/Markdown）
    │
    ▼
  Pipeline（抽取层）
    ├─ commands/extract-chapter.md   ← 9 步工作流编排
    ├─ skills/                       ← 15 个 V17 提取 skill + pool-field-inference
    ├─ scripts/create-tables.py      ← schema 创建
    ├─ scripts/insert-knowledge-points.py ← JSON manifest → SQLite
    └─ scripts/validate-pool.py      ← 6 个质量 gate（含覆盖 gate）
    │
    ▼
  pool/{course}.db     ← SQLite 知识池（整本教材一个库）
    │
    ▼
  View 层（渲染）
    ├─ views/first-pass/             ← 速览视图（command + skills + gates + templates）
    ├─ views/common/                 ← 共享 skills / gates
    ├─ pool/scripts/query-pool.py    ← Agent 用 JSON 查询
    └─ pool/scripts/print-graph.py   ← 学生用 Markdown 提纲
```

**一次抽取，多种呈现。** KP 是池中的原子资产，视图按需消费。Pipeline 和 View 独立演进。

## 设计哲学（光谱，非硬性立场）

完整哲学文档：`docs/design/philosophy.md`

| # | 轴 | 两端 |
|---|-----|------|
| 1 | 知识归顺度 | 唤醒自我 ↔ 规训自我 |
| 2 | 离原材料距离 | 近源 ↔ 远源 |
| 3 | 接收 ↔ 建构 | 成品交付 ↔ 原料拼装 |
| 4 | 呈现 ↔ 告知 | 窗户（让你看）↔ 替身（替你加工） |
| 5 | 无知测绘 ↔ 全知假象 | 标未知 / 争议 / 边界 ↔ 假装完整封闭 |
| 6 | 静止 ↔ 流动 | 允许停下 ↔ 持续推动 |
| 7 | 单脉络 ↔ 多脉络 | 一条主线 ↔ 多条视角 |
| 8 | 难度自主权 | 固定 1-5 ↔ 学生自定 |
| 9 | 错误价值 | 避免错误 ↔ 拥抱 productive failure |

5 条待工程化轴（工具可弃性、光滑↔纹理、完成感↔未完成感、解构/反学习、消费↔品味）已确认方向，**MVP 后讨论**。

## 项目结构（当前）

```
pipeline/
├── commands/extract-chapter.md       ← 9 步工作流 + 步骤 3 强制覆盖表 + 步骤 4.5 覆盖 gate
├── skills/                           ← 15 个 V17 提取 skill + pool-field-inference
├── scripts/                          ← create-tables, insert-kp, validate-pool
└── templates/pool-insert-manifest.md ← JSON 桥接格式规范

pool/
├── scripts/query-pool.py             ← Agent 用 JSON 查询
├── scripts/print-graph.py            ← 学生用 Markdown 提纲（叙述型，无 wiki link）
├── {course}.db                       ← SQLite 池（运行时，gitignore）
└── (output 目录不在 repo 内)

views/
├── first-pass/                       ← 速览视图（command + 4 skills + 4 gates + 3 templates）
└── common/                           ← 共享 skills + gates

intermediate/{course}/extraction/{chapter}/
├── 00_source/                        ← MinerU 抽取的源 markdown
├── 01_inputs/                        ← source-scope.md, source-material-inventory.md
├── 02_analysis/                      ← knowledge-points.md（含覆盖表）, relationship-analysis, consolidation, coverage-check.md
├── 03_plans/                         ← structure-plan.md
└── 04_checks/                        ← validation-report.md

docs/design/                          ← 5 个设计文档
```

## 抽取流程约束（关键）

1. **步骤 3 强制覆盖表**：`knowledge-points.md` 开头必须有 8 类候选来源覆盖表（definitions/formulas/theorems/conditions/models/diagrams-tables/code-fields/low-visibility-details）。Agent 不可跳过。
2. **步骤 4.5 覆盖 Gate**：Agent 产出 `coverage-check.md`，8 类二进制覆盖。有 FAIL 行 → 步骤 3 重抽。
3. **validate-pool.py kp-coverage 升级**：脚本读 coverage-check.md，FAIL 行 → ERROR exit 2。
4. **题不入池**：章节伴生题由视图层渲染时生成。课后习题 / 历年题 → 独立表（未来实现）。
5. **body 必填**：KP 正文从源材料提取（脚本自动采集）。fragile 必须人工填，Agent 不给默认值。

## 关键约定

- **kp_id 命名**：`{course}-ch{NN}-kp-{NNN}`（如 `dmath-ch06-kp-001`）
- **整本教材一个 DB**：`pool/{course}.db`
- **中间文件全量落地**：不审但留底，后续追溯
- **所有脚本 stdlib**：仅 Python 标准库，零外部依赖
- **print-graph.py 叙述型输出**：无 wiki link、无 "KP 索引/详情" 元标签、2 空行 block 间隔

## 当前进度

- ✅ Pipeline Create（schema + insert + validate + extract-chapter 工作流）
- ✅ 28 KP dmath ch06 池（真实教材 E2E，覆盖 gate PASS）
- ✅ 9 步工作流加固（步骤 3 覆盖表 + 步骤 4.5 覆盖 gate）
- ✅ fragile 字段 TEXT 重构
- ✅ 设计哲学 9 轴光谱锁定
- ✅ README + 设计文档 5 个

## 可用 Skill（设计辅助）

- `pipeline/skills/pool-field-inference/SKILL.md` — importance/difficulty/fragile 推断规则
- `pipeline/commands/extract-chapter.md` — 9 步抽取工作流
- `docs/design/philosophy.md` — 设计哲学光谱（9 轴 + 待工程化 5 轴）