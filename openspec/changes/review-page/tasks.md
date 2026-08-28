# review-page 任务

## 1. API 与数据

- [ ] `queries.due_list` 行带 `direction`；api `due_list` 支持 `limit`（默认 100）。
- [ ] `pull.select` / `pull_problems` 支持 `include_ids`（校验字符串列表；
      与 mode=all 组合返回 400；缺省行为不变）。
- [ ] `feedback` 端点与 `feedback.apply` 支持可选 `direction`（仅影响
      schedule 键；progress/current_state/signal 语义不变）。
- [ ] 单测：due direction/limit、include_ids 命中与 400、feedback 方向调度。

## 2. 复习页

- [ ] `pages.review_page` + `app._send_page` review 分支 + 第 4 导航项。
- [ ] 分组渲染（今天到期/未来 7 天/以后折叠计数）、行内徽标与相对天数、
      100 行上限与「还有 N 项」。
- [ ] 两条动手路径：queue-handoff、include_ids 直达练习。
- [ ] `review_page` CSS（组头/行/徽标/空状态，仅既有令牌）。
- [ ] 空 state：无到期项时一句话 + 指向练习页的入口。

## 3. 定向卡片会话

- [ ] JS 卡片流：正面→揭示→1–5 自评→feedback(direction)→下一张；
      sessionStorage 恢复；结束就地小结。
- [ ] contrasts/variant_of 邻居并列展示（`/kp/{id}` detail 已带 relations）。
- [ ] Node UI 测试：卡片渲染正反面、评调用携带 direction、邻居展示、
      空会话不出现入口、刷新恢复。

## 4. 路由与回归

- [ ] `test_ui_routes`：第 4 导航项断言更新、复习页 HTML 契约、
      无裸调度参数。
- [ ] 全量 pytest + Node + `openspec validate --specs --strict`。

## 5. 真实体验验收

- [ ] scratch 真实走查：49 条种子调度下分组正确、走完一轮卡片会话、
      截图自检清单逐条过（主行动可见/对齐轴/令牌/≤2 点击/空状态）。
- [ ] 归档变更 + changelog。
