# review-page：到期复习提醒面 + 定向卡片会话

按 `openspec/changes/archive/2026-08-29-review-page/` 实现（提案先行，PR #12）。

## 内容

- 第 4 个导航页「复习」：到期项按 今天到期（含逾期 N 项）/ 未来 7 天 分组，
  之后折叠为计数；行内为 标签 · 类型徽标 · 方向徽标 · `可以复习` 相对注记 ·
  动作。调度参数（ease/间隔/次数）零露出。
- 动手路径：知识点行走既有 queue-handoff；题目行走 pull 新增的
  `include_ids`（与 `mode: all` 组合返回 400）。
- 定向卡片会话（复习页内嵌）：按方向出正面 → 揭示 → 1–5 自评 →
  `feedback` 携带 `direction` 写该方向调度行；contrasts/variant_of 邻居
  并列展示；会话 tab 级可恢复；结束就地小结。
- API additive：`due` 行带 `direction` 且支持 `limit`；`pull.include_ids`；
  `feedback.direction`；`queries.review_overview` 供页面（到期+7 天+以后计数）。

## 验证

- 全量 pytest 310 通过（新增 API 与页面契约测试，第 4 导航项断言更新）；
  Node UI 44 通过（卡片流/方向反馈/恢复/无方向行无入口/普通题回归）。
- `openspec validate --specs --strict`：9 passed。
- 真实表结构副本 + 49 条种子调度实测：分组、徽标、两条动手路径、
  卡片会话全程（正面/揭示/评分），reverse 调度行 08-28→09-04 推进、
  正向行不动、信号如实记录；截图自检清单逐条过。
