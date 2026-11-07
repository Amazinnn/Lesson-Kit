## Why

所有者已裁定 **V1（样板图基线拼版）= 工作台视觉的正式基线版本**（`decisions.md` A-142 / A-143 / A-144，tag `v1-mockup-baseline`），但**产品还没有走到 V1**：外壳几何已按 V1 收口（Wave ① 四档 + 左栏重做 + 学习面纸形态），剩下四处**可见的功能差距**仍在，且它们正是"产品一眼看上去不像靶子"的主因：

1. **顶栏动作区在桌面端全空** —— 靶子的段三是「搜索 · 对话视图开关 · 夜纸开关 · Agent 对话」，产品桌面端一个都没有（版式 §2.2 / DRIFT-2 一直挂着"本轮不做"）。
2. **右栏会话平铺** —— 靶子按「今天 / 昨天 / 更早」分组（版式 §6.1）。
3. **「优先回看」条目没有状态点** —— 靶子的每条带一个状态几何（红 cross / 黄 / 蓝 ring）。
4. **左栏分组结构不同** —— 靶子首组叫「学习」且工作区身份在**顶栏段二**（"推导学习 / 高等数学"），产品是左栏顶部的「工作区」下拉 + 组名「页面」。

## What Changes

- **顶栏动作区落地**（新增交互，**须先落 spec 再实现**）：Agent 对话开关、主题（夜纸）开关、对话视图开关、搜索入口 —— 形态照 V1。
- **右栏会话列表按「今天 / 昨天 / 更早」分组**（版式 §6.1）。
- **「优先回看」条目加状态点**：颜色 + 几何双通道（`layout-spec` §6 的状态几何表）；**状态词表须先定**（`copy-table.md` §5 是契约词的地盘，新词按 `AGENTS.md` 纪律 2 先入 `docs/GLOSSARY.md`）。
- **左栏分组结构对齐 V1**：首组名「学习」；工作区身份上移到顶栏段二。
- **每波交付一张「靶子 | 改前 | 改后」三列对照板**（工具 `tools/walkthrough/view.py` 已在库）。

**不做**（明确划界）：

- **不动组件形态** —— 听 `component-spec.md` §4.30（A-115），V1 早于它 17 小时。
- **不动图谱页** —— 版式 §0.2 已把它划出范围。
- **不动请求序列与载荷** —— 「请求与持久化不变」仍是硬边界（本次核过：分支相对 main 的 454 个提交里 API 路由零增删、请求载荷零变化）。
- **不合并 main、不 push** —— 合并由所有者另行指示。

## Capabilities

### New Capabilities

<!-- 无。本变更不引入新的能力面，只把既有能力做到 V1 的形态。 -->

### Modified Capabilities

- `workbench-ui`:
  - 顶栏动作区的**行为**（哪些控件、做什么）—— 从"空"变为有；
  - 右栏会话列表的**分组**（`Agent rail presentation keeps the learning page primary`）；
  - 左栏分组结构与工作区身份的**位置**（`Three-column shell with navigation` / `Learner settings in the left rail`）；
  - 「优先回看」条目的**状态几何**（`Redundant state cues`：状态不得只靠颜色）。

## Impact

| 面 | 影响 |
|---|---|
| 产品代码 | `workbench/server/static/workbench.css`、`workbench.js`、`agent-ui.css`、`workbench/server/pages.py`（顶栏与左栏 markup）、`records.py`（会话分组数据） |
| 契约 | `openspec/specs/workbench-ui/spec.md` 的 delta（顶栏动作区 + 会话分组 + 左栏结构 + 状态几何） |
| 文档 | `docs/PRODUCT-MANUAL.md`（顶栏与左栏的用户可见说明）、`docs/GLOSSARY.md`（新增状态词）、`docs/ACTION-GRAPH.md`（若新增动作） |
| 不受影响 | 请求序列、载荷、持久化 schema、`pipeline/`、`pool/`、`workbench/data/`、`workbench/domain/` |
| 基线 | V1 = `openspec/changes/workbench-visual-language-v2/design-notes/mockup-baseline/v1.html`（tag `v1-mockup-baseline`） |
| 工具 | `tools/walkthrough/view.py`（三列对照板）已在库，可直接用 |
