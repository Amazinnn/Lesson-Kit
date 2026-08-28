# consolidate-practice-views 任务（实现会话执行）

> 本变更由设计会话（2026-08-29）定稿；实现前先读
> `docs/design/2026-08-29-doc-drift-audit.md` 与本目录 design.md。
> 交接要点见 `docs/superpowers/plans/2026-08-29-consolidate-practice-views-handoff.md`。

## 1. 拆除

- [ ] 移除 `review` 导航项与 `app._send_page` review 分支、`pages.review_page`
      / `card_session_html` / `time_view_html`。
- [ ] 移除复习页专属 CSS（保留徽标/水位等将复用的通用样式）。
- [ ] `workbench.js`：移除复习页区块，卡片流组件改造为可复用函数（供模式内
      轻会话调用）。

## 2. 练习页合流

- [ ] `pages.py`：练习页新增「今天」合流列表（计划行 ∪ 到期行，D1 排序去重；
      `reason_phrase` 按 D2）；`练习范围` 空态改为内联引导。
- [ ] 时间安排区块搬移至练习页学习安排旁（D3 双栏布局，端点不变）。
- [ ] 方向卡轻会话入口（D4）：提示条 + 原地卡片流 + feedback direction。
- [ ] CSS：合流行/双栏布局（仅既有令牌）。

## 3. 测试

- [ ] 路由测试回三页断言；合流列表契约（计划行/到期行/原因短语/动作、
      无裸调度参数）。
- [ ] API 测试保持：due direction/limit、include_ids、feedback direction、
      calendar。
- [ ] Node UI：合流列表渲染、卡片轻会话提示条与拒绝路径、时间视图搬移后
      渲染/预填/空状态、复习页不存在回归。

## 4. 验证与收尾

- [ ] 全量 pytest + Node + `openspec validate --specs --strict`。
- [ ] scratch 真实走查（种子 49 条调度 + 2 目标）：三页导航、合流列表排序
      与原因、卡片轻会话全程、时间视图并列布局；截图自检清单逐条过。
- [ ] `workbench-ui` Purpose 归档时改写为三页导航。
- [ ] changelog + 归档本变更。
