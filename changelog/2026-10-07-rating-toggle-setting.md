# 学习者设置：自评可整个关闭（判定折算 + 空 rating 卡死修复）

**日期：** 2026-10-07

## 变化

- **左栏新增「设置」区块**，第一项「练习与组卷显示自评」（默认开 = 现状）。偏好存浏览器
  `localStorage`（`wb_settings_<工作区>`，JSON）——工作台唯一的 localStorage 用法，其余客户端
  状态仍是会话级；设置跨标签页与重启持久，**下一轮开始时生效**，进行中的轮次保持开始时的模式。
- **`rating_mode` 新增 `"off"`，端到端贯穿**：练习开始与试卷开始按偏好上送；`active_practice` /
  `practice_runs` 如实存储；记录页标「关闭自评」。
- **关闭后自评影子都看不见**：练习页不再出现「自评时机（必选其一）」（也不再要求选择）、轮内
  永不出现反馈面板、做完不跳统一自评页、闪卡变纯翻卡（复用既有前后翻卡键）且不产生记录。
- **off 轮的推进动作是显式「下一题」**：提交 → 判分（横幅 + 正确项高亮）→（可选）查看解析 →
  点「下一题」走。没有任何自动推进。
- **判定折算学习结论**：off 轮客观题落库时一次写入进度 / 当前状态 / 排期（对 → mastered、
  错 → wrong，与 `RATING_PROGRESS` 同映射），**不写带评分的反馈事件**——「平均自评」「1–5 分布」
  不被合成数据污染；跳题仍记 stuck；综合题只记作答。
- **修掉一个真 bug**：自评输入的客户端校验 `rating < 1 || rating > 5` 对 `parseInt("") = NaN`
  双双为 false，空输入直达服务端被拒（「rating or note is required」），轮次看似卡死。两处校验
  （逐题自评与统一自评页）改为 `!(rating >= 1 && rating <= 5)`，空输入就地报错。

## 实现

- `pages.py::_left_column`（设置区块）+ 练习页 composer 的 `#next-problem`（藏在
  `feedback-area` 之前，off 且已作答时才出现）。
- `workbench.js`：`loadSetting` / `saveSetting` / `showRatingEnabled`；试卷开始 body 从空对象改为
  按偏好带 `rating_mode`（off / immediate）。
- `practice-flow.js`：`offNow()` 判定（读 `RATING_MODE_KEY === "off"`）；`ratingNow` / `batchNow`
  在 off 下恒假；开始路径写 `"off"`；`readyToStart` 不再要求自评时机；`finishExhausted` 与刷新恢复
  不走统一自评页；`syncNextProblem` 控制「下一题」显隐。
- `api.py`：`rating_mode` 校验集加 `"off"`（试卷开始；active practice 层本就只要求非空字符串）。
- `records.py`：轮次标签映射加「关闭自评」。
- `attempts.py::record_browser_attempt`：读取所在轮的 `rating_mode`，off + 判定非空时折算
  （结果带 `derived_state` 便于观察）；复用 `schedule_rules.after_result` 与 `learning_state.for_rating`。

## 边界

- 不加服务端偏好存储、不新增表；agent attempts 契约不变；immediate / batch 行为不变；
  判定折算不扩展到综合题；统计页对无评分轮次自然显示（不需要改）。
- 契约句更新：「只有显式自评才写学习记录」→「显式自评，或关闭自评轮次中客观题的判定」。
