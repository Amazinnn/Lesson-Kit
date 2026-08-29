# consolidate-practice-views 提案

## Why

当前工作台有四张「知识点列表 + 去练习」形态的视图（知识点清单、练习页今日队列、
复习页到期列表、练习范围空态提示），干着三个功能的活；「复习页」作为第 4 个导航页
与记录在案的三页导航决定（DISCUSSION-RECORD 专题 17、B6.2）相抵触，其内容
（到期列表 + 方向卡 + 日历）是对 2026-08-16 就挂起、从未定义的「复习页（前端）」
一名的自行填充。文档漂移审计（docs/design/2026-08-29-doc-drift-audit.md）结论：
复习页从未被任何在先文档定义或与 Yes/No 关联；到期摘要的原始设计位置就是
工作区主页（review-workbench v1「Forgetting-curve scheduling as background」）；
日历/任务量曲线的前端位置从未被记录。

本变更把视图收敛回三页导航；练习页以「准备练习列表」为唯一「真正要练的」清单
（= 用户显式选定的知识点），计划与到期降为按需拉取的候选建议；时间安排视图
移至练习页与学习安排并列；方向卡片 UI 全部拆除（调度数据与 API 保留）。

> 2026-08-29 实现会话改判：本提案最初按专题 18 方案一写成「自动合流今天
> 列表 + 模式内卡片轻会话」，随后被所有者改判为下述模型（记录见
> DISCUSSION-RECORD 专题 19），文档已同步改写。

## What Changes

- 移除第 4 个导航页「复习」（导航回练习/知识点/知识图谱三页）。
- 练习页新增「准备练习」区块：列表 = 当前知识点选区（`wb_kp_selection_{ws}`）
  的行视图，每行 = 知识点名 + 清除动作，与知识点页/图谱勾选双向同步；
  零新存储、零 schema 变化。
- 候选按需拉取：区块内一个「加今天要练的（N）」按钮（N = 候选数），点开才
  展开候选行；行 = 知识点名 · 一个短语 · 加入。来源 = 计划队列 ∪ 到期
  （`queries.review_overview`），映射到知识点级去重，每行只留一个短语
  （到期短语优先于计划短语）；已选定的知识点不出现在候选中。
  **字段极简是硬约束**：无徽标、无日期、无数字。
- 既有「今天先做」计划队列卡片解散，计划输出降为候选来源之一；
  「重算计划」按钮保留在候选区。
- 到期不做常驻视图（到期分组列表随复习页拆除）；UI 只到知识点级，
  题目行不进任何 UI。
- 「时间安排」（目标月历 + 14 天任务量柱状图 + 重日预填）从复习页原样
  搬移至练习页，与学习安排并列（宽屏并排、窄屏纵向）。
- 方向卡片 UI 全拆：提示条、卡片流、1–5 评分卡、`start-card-review` 入口
  全部移除且不迁移；每方向独立调度键与 `feedback.direction` API 保留，
  卡片类 UI 待真实使用出现后再议。
- **保留**的 additive API：`pull.include_ids`、`feedback.direction`、
  `queries.review_overview`（候选数据源与每日规划参考）、`/calendar` 端点、
  micro quiz 内容契约与本地判分。
- **移除**的 UI：复习页导航项与页面、到期日期分组列表、复习页时间区块、
  方向卡会话全部 UI。
- 顺手修复：练习页「开始练习」主按钮的禁用态样式（既有 UX 清单项）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workbench-ui`: 导航回三页；练习页新增「准备练习」区块（选区行视图 +
  按需候选）与并列时间安排；移除复习页需求。
- `review-workbench`: 到期以练习页候选区的按需建议形式出现（非常驻列表，
  对齐 v1「调度只做背景」）；「Directional card practice」需求移除，代之以
  仅调度语义的「Directional schedule entries」（每方向独立调度键、无卡片
  页与系统导向会话）；新增 include 过滤与 feedback 方向的显式需求
  （自 review-page 能力收编）。
- `calendar-workload`: 时间区块位置由复习页改为练习页。
- `review-page`（capability 级处置）：标注 **Deprecated**，被本变更取代；
  其中 include 过滤与方向调度的 API 要求收编进 review-workbench。

## Impact

UI 拆除与搬移集中在 `workbench/server/pages.py`、`workbench.js`、
`workbench.css` 与 `app.py` 页面分发；数据层 `queries.review_overview` /
`calendar_view` 保留复用；无 schema 变化；学习写入语义不变。已实现的
review-page / calendar-workload 两个变更中被本变更取代的部分随实现拆除，
其余（API、判分卡、种子样例）保留。文档（REQUIREMENTS / DISCUSSION-RECORD /
FUTURE-NOTES / ARCHITECTURE）随本变更同步修正漂移。
