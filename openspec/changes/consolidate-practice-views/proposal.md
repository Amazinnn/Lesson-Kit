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

本变更把视图收敛回三页导航，将到期提醒与今日计划合流为练习页的一张「今天」列表，
时间安排视图移至练习页与学习安排并列，方向卡片降为模式内可选轻会话。

## What Changes

- 移除第 4 个导航页「复习」（导航回练习/知识点/知识图谱三页）。
- 练习页新增统一「今天」列表：计划队列行与到期行合流排序，每行 =
  名称 + 人话原因（覆盖仍低 / 已到期 N 天 / 上次没记住）+ 直接动作；
  取代独立的到期分组列表与「练习范围」纯文字空态（空态改为内联的
  范围选择引导，不再指向另一页面）。
- 「时间安排」（目标月历 + 14 天任务量柱状图 + 重日预填）从复习页移至
  练习页，与学习安排并列（宽屏并排、窄屏纵向）。
- 方向卡片会话改为**模式内可选轻会话**：闪卡/判断模式开始时，若范围含
  到期方向行，提供「先翻 N 张到期卡」入口（ADR 0019 offered, never required）；
  判断题作答沿用 micro quiz 判分卡。
- **保留**的 additive API：`pull.include_ids`、`feedback.direction`、
  `queries.review_overview`（供合流列表复用）、`/calendar` 端点、
  micro quiz 内容契约与本地判分。
- **移除**的 UI：复习页导航项与页面、到期日期分组列表、复习页时间区块。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workbench-ui`: 导航回三页；练习页新增合流「今天」列表与并列时间安排；
  移除复习页需求。
- `review-workbench`: 到期提醒回归工作区主页（对齐 v1 原文，代码此前漂移）；
  方向卡会话定位为模式内可选轻会话；新增 include 过滤与 feedback 方向的
  显式需求（自 review-page 能力收编）。
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
