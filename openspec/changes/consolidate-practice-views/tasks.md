# consolidate-practice-views 任务（实现会话执行）

> 本变更由设计会话（2026-08-29）定稿、实现会话同日按专题 19 改判修订；
> 实现前先读本目录 design.md。
> 交接要点见 `docs/superpowers/plans/2026-08-29-consolidate-practice-views-handoff.md`
> （其 §二 已被本目录修订版取代，§三/§四/§五 的坑与验证关卡仍有效）。

## 1. 拆除

- [x] 移除 `review` 导航项、`app._send_page` review 分支、`pages.review_page`、
      `card_session_html`；删除 `workbench.js` 复习页与卡片会话整段（不迁移）；
      移除复习页专属 CSS（保留徽标/水位等将复用的通用样式）。
- [x] 删除 `pages.py` 成对重复的第一套死函数定义
      （`practice_page`/`_daily_plan`/`kps_page`/`graph_page` 的前者）。

## 2. 练习页新形态

- [x] 「准备练习」区块：选区行视图（`wb_kp_selection_{ws}` 渲染为
      知识点名 + ✕ 清除，与知识点页/图谱勾选双向同步）。
- [x] 候选按需拉取：「加今天要练的（N）」按钮（计数）+ 展开行
      （名称 · 一个短语 · 加入，D2 短语表）；计划 ∪ 到期知识点级去重、
      到期短语优先；已选定的不出现在候选；cap 20 + 「还有 N 条」；
      「重算计划」按钮迁入候选区。
- [x] 时间安排区块（`time_view_html` + JS）原样搬移至练习页右栏
      （D3 双栏布局，`/calendar` 端点不变）。
- [x] CSS：准备行/候选行/双栏布局（仅既有令牌）；主按钮禁用态样式修复。

## 3. 测试

- [x] 路由测试回三页断言；练习页结构契约（准备容器、候选按钮计数与
      单短语行、无裸调度参数、review 页不存在回归）。
- [x] API 测试保持：due direction/limit、include_ids、feedback direction、
      calendar。
- [x] Node UI：选区行渲染/移除/双向同步、候选加入-隐藏-计数、时间视图
      搬移后渲染/预填/空态。

## 4. 验证与收尾

- [ ] 全量 pytest + Node + `openspec validate --specs --strict`。
- [ ] scratch 真实走查（种子 49 条调度 + 2 目标，相对天数偏移）：三页导航、
      准备列表与勾选双向同步、候选加入-隐藏-计数、时间视图并列与窄屏
      堆叠、空态一句话一动作、禁用按钮样式；截图自检清单逐条过。
- [ ] `workbench-ui` Purpose 归档时改写为三页导航；「Directional card
      practice」按 delta 移除并由「Directional schedule entries」取代；
      FUTURE-NOTES 记「方向卡 UI 待真实使用再议」。
- [ ] changelog + 归档本变更；REQUIREMENTS / DISCUSSION-RECORD /
      FUTURE-NOTES / ARCHITECTURE 一致性检查。
