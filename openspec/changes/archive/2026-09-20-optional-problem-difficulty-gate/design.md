# design — optional-problem-difficulty-gate

## 上下文

- `knowledge_points.difficulty INTEGER CHECK 1-5` 是池里唯一活着的难度列；
  `questions` 是老表（注释写明 not populated）；`problems` **没有**难度列，
  flash_cards 也没有。
- KP 难度有现成量纲：`pipeline/skills/pool-field-inference/SKILL.md`（按
  knowledge_type 给默认 1-4、含证明/推导/综合 +1、跨章节综合 = 5、无法判断时
  记 notes 用默认 2）。
- 两条 KP 写入路径口径不同：legacy（`pipeline/scripts/insert-knowledge-points.py:147`）
  **可选**、缺失默认 2；workbench 门禁（`workbench/ingest/__init__.py:25` 的
  `KP_FIELDS` 与 `:1034` 的校验）**必填**、值域 1-5。`openspec/specs/` 里没有
  任何条目要求必填——必填是 8-29~8-30 门禁批次顺手收紧的实现事实。
- 「门禁只管形式，语义质量交给 Agent 后修」是本项目既有惯例
  （`pool-field-inference:96`：importance/fragile 没有合理性 gate）。
- 真题拟合联合立项排在 Check 首期真实使用之后（PENDING-DEFINITIONS）；
  本变更只攒第一批数据，不做拟合、不做消费者。

## Goals / Non-Goals

**Goals**

- 题有难度列（可空），三条入池通道共享同一可选语义与依据规则。
- 量纲沿用 KP 的 1-5 语义 + 题面映射，并落 GLOSSARY。

**Non-Goals**

- 不回填 303 道旧题（保持 NULL）；不写拟合算法；不做 UI 消费者；不落盘依据。
- 不动 legacy 路径的默认 2（AGENTS.md 分层铁律禁止改 `pipeline/` 行为契约），
  因此两条路径的差异以 spec 明示为准。
- 不把难度接进疼痛排序 / 日计划；`difficulty_mix` → `problem_type_mix` 只是
  改名纠错，不改变计划生成行为。

## 决策

### 一、可选 + 依据同现，只查形式

`difficulty` 可空；填了必须 int 1-5，且同一 item 必须有非空 `difficulty_basis`。
缺依据拒收整批——依据的作用是逼出一次真实判断（评分者至少要写下为什么），
而不是留作语料（见决策二）。语义正确性仍归独立审计与 Agent 后修。

### 二、依据不落盘

依据只在门禁校验时存在，不写池、不加列。批次快照（`pool/ingest/batch-XXX.json`）
保留被应用工件的原样内容，这部分沿用既有机制，不为依据另立承诺；将来拟合立项
若需要语料，由那个立项自己定义采集方式。

### 三、KP 必填 → 可选（合法路径内的统一）

把 workbench 门禁的 `KP_FIELDS` 必填集合里移出 `difficulty`，其余字段不动；
`_gate_content_patch` 的难度校验改为「填了才校验值域 + 依据」。legacy 脚本不动，
差异写进 spec 与 design（本条）。

### 四、列落在 problems，微测共用；闪卡不加

微测（`-mq-NNN`）本来就是 `problems` 表的行，同一列天然共用；闪卡在
`flash_cards` 表，且「回忆难度」与「题目难度」不是同一语义，硬套会污染数据。

### 五、量纲沿用 + 题面映射

同一套 1-5：1-2 记忆/识别（选择、判断、填空式回忆），2-4 有条件的直接应用
（计算、应用、方法套用），4-5 综合与构造（证明、建模、开放设计），跨章节综合 = 5。
与 `pool-field-inference` 的 KP 规则同向，具体映射写进 GLOSSARY「难度」条目。

## Risks / Trade-offs

- 依据不落盘 ⇒ 无法事后审计评分理由；取舍来自所有者判断（评分机制本身已由
  Agent 承担，且依据的语义价值在拟合立项前无法评估）。风险留给拟合立项的
  定义流程。
- KP 门禁放宽后，新 KP 可以完全不带难度；缓解：生成侧（pool-field-inference
  的任务清单）仍要求逐项给出，弃权需要理由。
- 两条写入路径的差异（legacy 默认 2 / workbench 可空）会长期存在；已写进 spec，
  不再算隐藏事实。
