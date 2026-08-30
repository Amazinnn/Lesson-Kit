# Check Agent 产出链完整交付 · 开工问卷（2026-08-30）

**Purpose:** 队列④收尾反馈「什么都实现了一点，但没实现完全」后，为「完整开发结果」一轮钉死范围与验收标准（新项目开工检查清单 阶段 0）。

**From:** ZCode（开发 Agent） — **To:** 所有者 Amazinnn — **How your answers will be used:** OpenSpec change `harden-check-agent-chain` 的 proposal 边界与 benchmark 定稿（design.md）的事实来源；DISCUSSION-RECORD 专题 23 存档。

## Context

Check 管线（批次 id + 整批回滚 + 桥 check_ingest 动作）已实现并走查通过，但演示暴露两点：对话里的出题回复来自 stub 演示脚本，真实 codex/claude 能否产出合规 manifest、被拒收后能否自行修正——未验证；门禁裁决结果不回给 Agent（无反馈回路）。所有者按《新项目开工检查清单》要求本轮交付「完整的开发结果，绝不只是小修小补与小型功能试水」，并指定用 to-questionnaire 讨论范围。

## How to answer

已在对话中逐题作答（2026-08-30）。答案逐字记录如下，作为本轮 scope 与验收的唯一权威。

## 一、打包范围

### 这轮「完整开发结果」的打包范围包含哪些？

**答（原话）：** 「真 Agent 产出链+benchmark, 以及除了出题以外的所有面向Agent的所有CLI。顺带一提，agent产出的题/卡自带标签等完备格式（不然怎么叫CLI），只是需要被校验。」

**解读（开发 Agent 落笔，所有者计划批准时确认）：**
- 包含：真 Agent 产出链 + benchmark（核心）；manifest 完备格式——题/卡 items 自带 topic_label 等标签字段，门禁校验；面向 Agent 的 CLI 面补全（综合题出题除外）。
- 不做：界面闭环（未提及）、综合题出题配方（「除了出题以外」）、候选表 DROP。

## 二、benchmark 规模

### 成功率分布按多大规模跑？

**答：** 「codex 10×2 单链路」——codex 单 provider，闪卡/微题各 10 轮（hold-out KP），共 20 轮真调用。

## 三、成功判定

### 一轮 run 怎么算「成功」？

**答：** 「严格：首轮成功率≥60%」——首轮（未经修正）合规入库才算成功，每种 kind 首轮成功率 ≥60% 为达标线；修正后最终成功率另行报告（信息性，不计达标）。

## 四、真实池验收

### 副本 benchmark 达标后，要不要由你亲自在真实池对话出题入库一次？

**答：** 「你完事之后由我亲自实验。」——benchmark 达标后，所有者在真实工作区亲自出题入库作为最终验收；交接文档须写清操作路径。

## Anything else?

所有者补充工作法约束：「依然鼓励你使用并行不多于2个Codex作为Sub Agent。」——任意时刻 ≤2 个 codex 并行、文件集不交叉、停掉的分身先核对残留再接手（沿用 memory 反馈规则）。
