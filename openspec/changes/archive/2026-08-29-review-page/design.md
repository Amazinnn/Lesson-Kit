# review-page 设计

## D1 提醒面，不是任务队列

review-workbench 红线：调度只影响排序，永不隐藏/锁定/拒绝。复习页因此：

- 只读展示 + 两个主动作入口，没有「必须完成」状态、没有进度压迫；
- 行内提示统一用 `可以复习`（到期/逾期同理，逾期行加「已过期 N 天」的
  相对天数，不渲染 urgency 颜色恐吓）；
- 调度参数（ease/interval/repetitions）在页面任何位置都不出现。

## D2 分组与排序

```
今天到期      due_at <= today      （含逾期，逾期行标「已过期 N 天」）
未来 7 天     today < due_at <= +7d
以后          > +7d                （折叠为一行计数，不展开）
```

组内按 due_at 升序、同日按 item_type/item_id 字典序（确定性，无随机）。
列表上限 100 行 + 「还有 N 项」计数（避免长页）。

## D3 到期项的两条动手路径

- **知识点级行**：行尾「去练习」→ 既有 queue-handoff（`data-queue-kp-ids`
  写入选区 → 练习页选模式）。不加新端点。
- **题目级行**：行尾「练这道」→ `/pull` 新增 `include_ids`：在 kp 范围
  （同行的关联 kp）∩ include_ids 内拉题。`pull.select` 过滤发生在模式
  判定之后、exclude 之前；`include_ids` 与 `mode=all` 组合时直接报 400
  （语义冲突）。缺省 None 行为不变。

## D4 定向卡片会话（复习页内嵌，不新开页）

- 入口：页首「开始卡片复习」主按钮（有到期方向行时才出现）。
- 会话取**到期方向行**（不限 memory-recall 类型——机制通用，spec 的
  memory-recall 要求只是其适用子集）；每张卡：
  - 正面：正向=知识点名 → 揭示=body 摘要；反向=body 摘要 → 揭示=知识点名；
    题目卡（如有方向行）按题目文→解析。
  - 揭示后 1–5 自评 → `feedback` 带方向写该行调度 + 现有 signal/progress
    语义（方向仅影响 schedule 键，progress/current_state 仍按 item 维度）。
  - `contrasts`/`variant_of` 邻居（按 relations）在卡片下方并列一行展示。
- 会话状态存 tab 级 sessionStorage（`wb_card_session_{ws}`：剩余行索引、
  已评计数），刷新可恢复，关 tab 即弃（与练习会话同约定）。
- 结束页：就地显示「本轮卡片完成 N 张」+ 回到列表，不跳 session-end
  （卡片会话不产生待补评分队列）。

## D5 API 形状

- `GET /api/w/{name}/due?limit=N`：行增加 `direction`（缺省 `""` 渲染为
  正向）；`limit` 缺省 100。
- `POST .../pull` body 可选 `"include_ids": [...]`（字符串数组校验）。
- `POST .../feedback` body 可选 `"direction"`（字符串，缺省 `""`）；
  `feedback.apply` 的 schedule 读写按方向键，其余不变。

## D6 视觉（走查清单的直接回应）

- 页首两段式：标题行 + 一句摘要；主按钮「开始卡片复习」第一屏可见；
  无到期卡片时该按钮不出现（诚实空状态）。
- 列表行：`标签 · 徽标(类型) · 徽标(方向) · 相对时间 · 动作`，grid
  固定列轴（走查发现的「三列无对齐轴」不再犯）；每行徽标 ≤ 2。
- 新 CSS 只用既有 `--dsw-*` 令牌；新增类：`.review-group-head`、
  `.review-row`、`.badge`（类型/方向共用，方向徽标用边框色区分）。
- 练习会话进行中的注意力收敛不在本变更（属练习页改造，已记入 UX 清单）。
