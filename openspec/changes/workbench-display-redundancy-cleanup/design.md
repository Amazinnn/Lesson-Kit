# design — workbench-display-redundancy-cleanup

## Context

缺陷证据与动机见 proposal.md「Why」。本 change 只改**展示层文案/字段**，不改请求序列/载荷
（G-1）、不改 Tab 序列（G-8）、不改来源显隐偏好、不动图谱（范围外）。
组件形态权威 = component-spec §4.30（A-115）；文案权威 = 同 change 的 `copy-table.md`；
术语权威 = `docs/GLOSSARY.md`。UI 为服务端渲染（`pages.py`）+ 无构建原生 JS/CSS（`static/`）。

## Goals / Non-Goals

**Goals**
- 逐项移除 A1–A6、B1–B5 的注释型字段，落地 specs delta 的两条 Requirement。
- 把「零注释型字段」沉淀为可复用纪律，写入 component-spec §3、copy-table、GLOSSARY、
  PRODUCT-MANUAL、ACTION-GRAPH，防复发。
- 状态语义一律改走几何 + 宿主 `aria-label`，消除 DRIFT-CUE-1。

**Non-Goals**
- 不新增任何交互面（不实现 component-forms 的 4 条 B 类）。
- 不改数据/schema/API；不移除任何 persisted provenance 或可用功能。
- 不重排版式、不调 token、不碰图谱页。

## Decisions

1. **移除而非改写**：注释型字段一律删除，不"换个说法保留"。理由：其内容本身非学习者所需，
   改写只是换一种冗余。例外见决策 4（来源证据串有价值，去标签保留值）。

2. **「详情」按钮的 pin 行为保全**（A1 唯一非纯展示功能）：`part-practice.js:83` 的「详情」按钮
   真实功能是"点击钉住小问状态卡"。移除文字按钮后，把"钉住"动作迁到**已存在的小问状态卡本身**
   （卡可点击/可聚焦以切换 pinned），`.paper-dot` 保持 hover/focus 弹卡。
   理由：不丢既有 pin 能力（以旧为优先），又不留注释型文字标签。
   替代方案（否决）：直接删除 pin —— 违反"不移除可用功能"。

3. **状态文字 → aria-label**（A1/B4，DRIFT-CUE-1 一致结果）：
   题号格、Agent 里程碑的状态只由 marker 几何/outline 承载 + 宿主 `aria-label` 宣告；
   删除相邻可见状态文字。**前置条件**：移除可见文字前，确认目标元素 `aria-label` 已含该状态
   （`.paper-dot` 已有 `"第N题，正确，当前题"`；里程碑需补 `aria-label`）。
   否决方案：保留文字作为"可达性冗余" —— 与 §4.15「零文字」冲突，且 DRIFT-CUE-1 已裁定收紧。

4. **「来源：」去前缀保留证据串**（A5）：证据串本身对学习者有价值，只删硬编码「来源：」字段名
   前缀，改为自然呈现（如小字引用块，无「来源：」标签）。来源**显隐**仍完全由
   `Question source display preference` 控制，persisted provenance 不变。

5. **判定/状态串口径统一**（A4/A6，DRIFT-CUE-2）：两流统一为自然陈述句
   （`practice-flow.js:838` 的「回答正确。」风格），去「判定：」等字段名前缀；
   措辞以 `copy-table.md` 为准。**A6 收窄（实现期裁定，依 change 自带 ADDED 要求
   "移除字段 SHALL NOT remove the underlying data"）**：`part-practice.js:6-10` 的
   「答案：/过程：」是区分"答案维度"与"过程维度"两个真实评分的**语义标签**，删除会丢失
   该区分（属移除底层数据），故**保留不删**。A6 真正的冗余——判定口径不一——已由 A4 统一。
   遗留观察项见 Open Questions。

6. **设置条目具象名**（B3）：`pages.py:1142` 的「设置」条目改为具象名，对齐靶子
   `shell.html`（如「偏好与主题」），消除与组名同字。分组标题「设置」保留。

7. **文档沉淀落点**：反模式命名为「注释型字段（annotation-type field）」——
   先在 `docs/GLOSSARY.md` 建条目（正式文档引入新名词须先定义）；纪律正文进
   component-spec §3 通用规则 + `copy-table.md`；用户可见说明进 PRODUCT-MANUAL；
   退役的「详情」入口登记 ACTION-GRAPH。

## Risks / Trade-offs

- [移除可见状态文字降低可达性] → 每处移除前确认 `aria-label` 已覆盖；用屏幕阅读器/焦点遍历验证。
- [pin 迁移引入回归] → 决策 2 落地后手测 hover/focus/点击钉住三态；reduced-motion 下仍可操作。
- [A6 措辞改动与 copy-table 契约冲突] → 改前 grep copy-table 对应词条，冲突则改 copy-table 再改代码。
- [删除 eyebrow/kicker 后卡片层级变平] → 仅删注释型标签，保留标题层级；渲染后核对三列对照板。

## Migration Plan

纯前端展示层改动，无数据迁移。按 A 组（练习页）→ B 组（壳层/导航）→ 文档沉淀分批提交，
每批可独立验证/回滚（单文件 revert）。归档顺序：v2 先、graph-node 后（沿用既有约束，本 change 不改）。

## Open Questions

- **A6 遗留观察项（不阻塞本 change）**：`part-practice.js` 状态串里 `answer_conclusion`
  （「答案：正确」）与 `objective_verdict`（裸「· 正确」）可能重复表达同一判定。是否合并、
  如何自然化属评分语义，须由 `copy-table.md` / 领域权威确认后再动——本 change 不在无确认下
  删除任一通道（避免移除真实数据）。已保留为待确认项，不影响已提交 spec 的 SHALL 边界。
