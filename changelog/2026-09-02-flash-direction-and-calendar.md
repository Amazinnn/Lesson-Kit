# 闪卡交互修订与日历自适应（2026-09-02 所有者走查）

- 闪卡方向收敛为会话级 `正向 / 反向`（默认正向）：开练前选定、会话内固定；
  删除混合偏好与会话中 ⇄ 方向交换按钮；双向卡在正向会话出正向、反向会话出反向；
  单向卡在反向会话仍按正面提问。
- 所有闪卡统一渲染为完全重合的两张牌（提示面在上、另一面完全遮蔽）；点击
  「揭示另一面」时上牌逆时针漂移停住、下牌顺时针漂移后从下方滑出完整可见
  （轻微倾斜保留蒙德里安质感）；`prefers-reduced-motion` 直接呈现终态。
- `pull-cards` 的 `direction_mode` 校验收敛为 `forward | reverse`（mixed 返回 400）；
  方向数据模型、`(card, direction)` 调度行与 `exclude_directions` 拉取排除不变。
- 练习页右栏月历去掉 560px 钉死宽度与横向滚动，7 列自适应铺满栏宽；目标条
  保持省略号 + 悬浮全名。
- 同步 openspec：`revise-flash-card-direction-interaction`（flash-card 会话方向 +
  workbench-ui 叠牌呈现）。
