# IMPL-N2 — 契约一致性核对（只读审计，不改任何文件）

> 对应 `AGENTS.md` 的「契约协调」与 `tasks.md` **28.5**（spec 补正与冲突收敛）的**前置**。
> **只新建** `openspec/changes/workbench-visual-language-v2/contract-consistency-report.md`。
> **不修改任何其它文件。**

## 背景
本变更动了两份 spec delta（`workbench-ui` / `workbench-settings`）、一份
`calendar-workload` delta，另有 `component-spec.md`（28 组件 × 8 态）与 `design.md`（D-1…D-16）。
实现已经跑到 110/167。**现在要做的是：把「文档说的」与「代码做的」逐条对齐，列出所有不一致。**

## 要核对什么
1. **spec delta → 实现**：两份 delta 的每条 Requirement / Scenario，
   找**实现里没有对应行为**、或**行为与条款不一致**的地方。
   逐条给：**条款位置 → 实现落点（file:位置）→ 一致 / 不一致（附证据）**。
2. **component-spec.md（28 组件 × 8 态）→ 实现**：每个组件的**形态与状态**是否与规格一致；
   哪些状态**只定义了没实现**、哪些实现**多了规格没有的形态**。
3. **design.md D-1…D-16 → 实现**：每条设计决策的**关键约束**（冻结项、允许清单、
   禁止项）是否被守住。
4. **权威表 `night-paper-tokens.md` ↔ 实现**：token 的**定义集合 vs 引用集合**求差
   （未定义却被引用的 / 定义了没人用的），亮/夜两套值是否成对。
5. **GLOSSARY / PRODUCT-MANUAL 的名词**是否在实现里**同名同义**（不许实现里另起一套叫法）。

## 硬约束
- **只新建** `contract-consistency-report.md`。**不修改任何其它文件**——
  **发现不一致也不要自己改**（代码、spec、docs 一律不改），**列进报告**，
  由主会话决定怎么改（可能涉及 spec delta、docs 同步、代码修正三条路）。
- **不要**改 `docs/` / `openspec/` 下其它文件 / 产品代码（`workbench/` / `pool/` / `pipeline/`）。
- ⚠️ 走查期间**另有 agent 正在并行改产品代码** ⇒ 报告里写明**你那一轮对应的代码状态**
  （`git rev-parse HEAD`），并把「哪些结论可能因并发改动而过期」标出来。
- 结论必须有**可复核的证据**（file:位置 / grep 输出 / 实测值），
  **不许**写「大致符合」这种没法核的话。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
openspec validate workbench-visual-language-v2 --strict
```

## 落盘纪律与回报
- 一个 commit，只 `git add` 那个报告文件，**不要 `git add -A``**。
- 最终回报（中文）必须复述：已落盘路径 + commit 的内容 +
**不一致清单（逐条：位置 → 证据 → 建议修哪一边）** +
**一致的部分的覆盖统计**（各查了 N 条、M 条不一致）+
**那一轮的代码状态** + 待裁决项。
