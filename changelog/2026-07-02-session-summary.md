# 2026-07-02 会话进度总结

**从 V17 方法论试验田到 lesson-kit MVP —— 两系统架构 + 真实教材 E2E**

## 会话产出概览

14 commits（`15a246b` → `02a0d61`），涵盖：设计哲学、Pipeline Create、Print 视图、fragile 重构、流程加固、稳定性清理。

## 设计层：哲学光谱 + 抽取流程

### 设计哲学 9 轴锁定

见 `docs/design/philosophy.md`。从「帮你回到源材料」的核心命题出发，扫描 10 个商业产品 + 50 个 GitHub 开源项目后，确定 9 条核心光谱轴：

1. 知识归顺度（唤醒自我 ↔ 规训自我）
2. 离原材料距离（近源 ↔ 远源）
3. 接收 ↔ 建构（成品交付 ↔ 原料拼装）
4. 呈现 ↔ 告知（窗户让你看 ↔ 替身替你加工）
5. 无知测绘 ↔ 全知假象
6. 静止 ↔ 流动
7. 单脉络 ↔ 多脉络
8. 难度自主权
9. 错误价值（避免 ↔ 拥抱 productive failure）

5 条待工程化轴已确认方向（工具可弃性、光滑↔纹理、完成感↔未完成感、解构/反学习、消费↔品味），MVP 后讨论。

### 抽取流程加固（根因修复）

dmath ch06 E2E 暴露：Agent 凭感觉提取，只抽到 22 KP（严重低于用户 765 行教案的预期覆盖）。非补 KP 能解决的问题——根源在**流程层**。

**修复方案：**

1. **步骤 3 强制覆盖表**（`extract-chapter.md`）：Agent 在 `knowledge-points.md` 开头必须写 8 类候选来源覆盖表（definitions/formulas/theorems/conditions/models/diagrams-tables/code-fields/low-visibility-details）。每个类别计候选数 + 代表性条目。

2. **步骤 4.5 覆盖 gate**（新增）：Agent 产出 `coverage-check.md`——8 类 × PASS/FAIL。任何类计数为 0 → FAIL → 回步骤 3 重抽。

3. **validate-pool.py kp-coverage 升级**：WARNING → ERROR。脚本读 coverage-check.md，解析 Markdown 表格，FAIL 行 → exit 2。

验证：修复前 22 KP（3 类未覆盖），修复后 28 KP（8 类全 PASS）。

## 工程层

### Pipeline Create（`pipeline/`）

| 脚本 | 用途 |
|---|---|
| `create-tables.py` | 4 表（含 body/fragile TEXT）+ 6 索引，`--force` 重置 |
| `insert-knowledge-points.py` | JSON manifest → SQLite，枚举验证，`--upsert` |
| `validate-pool.py` | 6 个 gate（含覆盖 gate），ERROR/WARNING 分级，`--json` 输出 |

Workflow：`pipeline/commands/extract-chapter.md`（9 步，Agent 执行 + Python 脚本机械操作）。

### Print 视图（`pool/scripts/print-graph.py`）

叙述型 Markdown 提纲，面向学生。

- 字段展示：`knowledge_item`（粗体）、`body`（正文）、`fragile`（独立段，如非 NULL）
- 隐藏：kp_id、importance、difficulty、knowledge_type、learning_action、source_location
- 无 wiki link、无 "KP 索引"/"KP 详情" 元标签
- 标题层级：H1 章 → H4 节组 → 粗体 KP 名
- 块间 2 空行间隔

### Schema 变更

- `fragile INTEGER DEFAULT 0` → `TEXT`（NULL = 不脆弱，非 NULL = Markdown 描述）
- 新增 `body TEXT` 列（KP 正文，从源材料采集）

### 真实教材 E2E

- 课程：离散数学（dmath）Chapter 6
- 源材料：PDF 英文原版（MinerU precision extract → Markdown）
- KP 池：28 KP（dmath-ch06-kp-001 ~ 028）
- 覆盖 gate：8/8 类 PASS
- 输出：in-memory 309 行 Markdown 提纲（all body filled，0 wiki link，0 fragility note）

## 设计文档状态

| 文档 | 状态 |
|---|---|
| `docs/design/philosophy.md` | ✅ 核心光谱锁定，待工程化轴挂起 |
| `docs/design/kp-pool-modular-views.md` | ✅ schema + body/fragile 字段已更新 |
| `docs/design/pipeline-create-design.md` | ✅ 设计完成（9 步工作流） |
| `docs/design/print-graph-design.md` | ✅ 重写为叙述型，字段集最新 |
| `docs/design/view-layer-design.md` | ✅ 首版已提交 |
| `docs/superpowers/specs/2026-07-02-fragile-text-redesign-design.md` | ✅ spec 已提交 |

## 未落地

| 项目 | 状态 |
|---|---|
| 题目池（textbook_exercises / exam_questions 表） | ⚠️ 设计完成，未实现 |
| CRUD 后两件（Update / Delete） | ⚠️ 未设计 |
| problem-set 视图 | ⚠️ 未设计 |
| INDEX.md（Print 课程级 MOC） | 推迟 |
| 5 条待工程化轴的具体落地 | MVP 后 |
| Hook 自动化 | 推迟 |
| 第二个教材验证（跑不同课程/章节） | 未做 |

## 下个会话建议起点

1. **对照用户教案跑全流程**：拿 dmath ch06 真实 PDF + 用户已有教案做 output 质量对比
2. **实现题目池**：textbook_exercises 表 + scripts
3. **跑第二个教材验证**：不同的学科、不同教材类型，测试抽取流程的泛化能力
4. **Update/Delete CRUD**：最小的可操作性——修改单个 KP 的 body/fragile