# IMPL-W5 — 第 28 组契约同步（28.1–28.5）：职责文档与 spec 补正

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 28 组 28.1–28.5**。
> **只改文档与 spec delta，不碰任何产品代码。**

## 前置（自己核实，不要相信任何人的口头汇报）
- 第 3 波的产品代码**已大量落地**（`git log --oneline -30`）。
  **动手前先读实现现状**，文档要写**已实现的事实**，不是计划。
- 关键已落地事实（已由主会话核实）：
  - 设置视图 `/w/{name}/settings` 已实现（主题 / 阅读字面 / 动效 / 声音四项外观偏好，
    按工作区存 `wb_settings_<工作区>`，跨工作区独立）；
  - 主题默认跟随系统 `prefers-color-scheme`，显式选择优先（`decisions.md` **A-11**）；
  - 夜纸值集已落地（11 个角色 token + 5 层表面 + 5 级墨阶）；
  - 阅读面 `.wb-reading` 已落地（17px / 1.75 / 38em / 段距 0.7em / 标题 22·19·17），
    题面变体 `.wb-reading--stem` 同刻度（**A-6**：题面与正文同档）；
  - `.rich-text` 的 HTML 挂载点**已全部迁到 `.wb-reading`**（6.2 / 6.3 的 JS 与 PY 段），
    但 **`.rich-text` 的 CSS 规则尚未删除**（2.3 收尾留到下一波）⇒ 文档要写**当前事实**，
    不要写成「已彻底退役」；
  - scope-tray 死代码**已归零**（14.1，`grep -rn "128px\|scope-tray" workbench/` 命中 0）；
  - 静态资产目录已新增 `assets/icons/` · `assets/empty/` · `assets/motion/` ·
    `assets/audio/` · `fonts/`（**A-40** 是唯一口径）；
  - 新增工具目录 `tools/`（`tools/graph-layout-diff.js` + `tools/graph-baseline/` ·
    `tools/walkthrough/`），**是开发工具，不是产品运行时**。

## 硬约束
- **只改这些文件**：
  `docs/GLOSSARY.md` · `docs/PRODUCT-MANUAL.md` · `docs/ACTION-GRAPH.md` ·
  `docs/action-graph/L3-actions.md` · `docs/ARCHITECTURE.md` ·
  `openspec/changes/workbench-visual-language-v2/specs/workbench-ui/spec.md`。
- **绝不改**产品代码（`workbench/` / `pool/` / `pipeline/` / `lessonkit.py`）——
  **另有几个 agent 正在并行改那些文件**。
- **不要**改 `tasks.md`（复选框由主会话勾）、**不要**改 `decisions.md` /
  `contract-drift.md` / `design.md` / `design-notes/`（主会话统一维护）。
- **不要**改 `docs/PENDING-DEFINITIONS.md`（**漂移提示写在 `HANDOFF.md`，不要往那里追加**）——
  注意：工作区里 `docs/PENDING-DEFINITIONS.md` 有**别人在 2026-10-18 的未提交改动**，
  **不要提交它，也不要还原它**。
- `docs/audits/` **只放带日期的快照**，不得当新规范。

## 要做什么

### 28.1 `docs/GLOSSARY.md`
- 核对「柔和蒙德里安 / Soft Mondrian」条目**已被改写为「暖色 + 现代圆润」**定义
  （不得再把「暖纸色 + 深色结构线」写成该语言的定义）。
- 核对 13 条新词条齐全：纸面层级 / 夜纸 / 冗余状态通道 / 主题偏好 / 阅读字面 /
  动效偏好 / 声音偏好 / 工作台设置视图 / 静物插画 / 台灯转场 / 少字原则 /
  图案适配原则 / 静物插画（最后一条与前面重复 —— **核对词表里是不是真有两个同名条目**，
  若有重复条目，按 GLOSSARY 的既有规范处理（合并或删一个），并**在回报里说明**）。
- 与 `tasks.md` 的用词逐条一致。**缺项补齐、旧措辞残留清掉。**
- ⚠️ **新名词必须先在 GLOSSARY 建条目**才能进正式文档（AGENTS.md 纪律 2）。
  本波若出现新名词（如「硬阴影」token、「通用骨架占位」），**先建条目再引用**。

### 28.2 `docs/PRODUCT-MANUAL.md`
- 补「工作台设置视图」章节，**含这条定案**：「按工作区存储、跨工作区独立、
  **换工作区要重设外观**」。
- 按**最终实现**写明**阅读面字号刻度**（17px / 1.75 / 38em；题面与正文同档 ——
  `decisions.md` **A-6**）。
- **保留**知识点正文「宽行距 + 单侧结构线」的既有硬性表述（`docs/PRODUCT-MANUAL.md:129-130`）。
- 补本波已落地的**用户可见行为**（只写已实现的）：
  练习页三件套（题面独立纸 / 解析同级 / 作答区沉底块 + 「你的作答」标签）·
  记录中心卡片流与仪表盘 · 知识点页分组卡片 + 状态圆点 + 章节计数条（**无百分比**）·
  连对三级计数器与火苗簇 · 日常档 / 里程碑档两档庆祝（**里程碑目前只有「全对」能触发**，
  另一条件因缺数据来源恒不成立 —— `contract-drift.md` **CD-167**）·
  骨架屏与视图转场 · 四个关键反馈音效 · 夜纸主题。
- ⚠️ **组卷报告的「可用题数少于请求量的知识点」显示的是知识点 id**
  （既有缺陷，`contract-drift.md` **CD-166**）—— 手册要不要写明由你判断，
  写了就写**事实**（显示 id），不要写成显示名字。

### 28.3 `docs/ACTION-GRAPH.md` + `docs/action-graph/L3-actions.md`
按任务书原文登记：
- **新增动作**：设置视图 · 主题切换 · 连对升级反馈；
- **退役动作**：scope-tray 死预留与死 CSS 清理；
- **改级动作**：`.rich-text` → `.wb-reading`。
- 既有的「打开 / 关闭工作台设置视图」「修改外观偏好」两条**状态要从「已定义未实现」
  改成「已实现」**（本波已落地）。
- 沿用该文件既有的**表格格式与措辞风格**，不要另起一套。

### 28.4 `docs/ARCHITECTURE.md`
- 更新**静态资产目录结构**：`assets/icons/` · `assets/empty/` · `assets/motion/` ·
  `assets/audio/` · `fonts/`（**与仓库实际一致** —— 自己 `ls` 核对，不要照抄任务书）。
- 补**设置视图路由**（`/w/{name}/settings`）。
- 把「普通 Paper 题目与知识正文共享主阅读层级」这条既有契约标注为**已兑现**。
- ⚠️ `tools/` 是**开发工具**（图谱基线取证 + 走查执行器），**不是产品运行时** ——
  要在架构文档里说清它与产品目录的边界（别让后人以为 `tools/` 要打进包）。

### 28.5 spec 补正与冲突收敛
- 把 **D-14 的 5 档日历阈值**（0 / 1 / 2–3 / 4–7 / ≥8，源自 `records.py`）写进
  `specs/workbench-ui/spec.md` 的 Records center 需求，
  并补 **`.level-0` 的 CSS 与页面图例**（CSS 与图例属产品代码 ⇒ **只做 spec 与文档那一半**，
  CSS 与图例登记成「待实现」并写进回报，由主会话派活）。
- 核对 `design.md` **D-5** 与 spec delta 关于 stem 字号的表述**一致**
  （题面与正文同为 **17px / 1.75 / 38em** —— A-6 的结论）——
  这是**一致性核对**而非冲突校正。

## 验证
- 跑 AGENTS.md 四条验证命令（确认没碰坏别的）：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- `openspec validate workbench-visual-language-v2 --strict` 仍 valid。
- **自检**：本波你改过的每个文档里，**不得出现产品里不存在的功能**；
  每条新写的用户可见行为，都要能在实现里指出落点（文件 + 位置）。

## 落盘纪律与回报
- **小步提交**：一个职责文件一个 commit，**只 add 你改的那几个文件**，
  **不要 `git add -A`**（尤其**不要**带上 `docs/PENDING-DEFINITIONS.md`）。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 + **28.1–28.5 逐条的完成情况** +
  **GLOSSARY 新词条清单**（新增/合并/删除各有哪些）·
  **PRODUCT-MANUAL 新增章节清单** + **ACTION-GRAPH 登记的新增/退役/改级动作逐条** +
  **ARCHITECTURE 的目录树与实际核对结果** + **28.5 里 CSS 与图例那半的待实现清单** +
  四条验证命令结果 + **待裁决项**。
- 数字与事实一律以**当场核对出来的现状**为准，不要照抄任务书里的旧描述。
