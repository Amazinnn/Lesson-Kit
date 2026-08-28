# 交接文档：consolidate-practice-views 实现（2026-08-29）

> 给下一个实现对话：本文档自包含，配合
> `openspec/changes/consolidate-practice-views/`（提案/设计/任务）使用。
> 开工前先复述三件事：**分层方向（Shell → Domain → Data 单向）、兼容边界
> （用户可感知行为以旧为优先；数据格式开发期可改）、scope 边界
> （需求先落文档再动代码）**（AGENTS.md 全文必读）。

## 一、现状（截至本交接）

- 仓库 `Amazinnn/Lesson-Kit`，本地 main 与 origin 同步，工作区干净
  （3 个历史未跟踪文件属正常：`.lessonkit/plan.json`、
  `workbench/_claude_*_task.txt`，已 gitignore）。
- 最近合入（全部 rebase 线性合并、CI 绿）：
  - micro-quiz 内容契约（`problems.practice_modes` / `micro_quiz` 两列、
    `domain/micro_quiz.py`、`wb ingest recipe micro-quiz`、练习页按题型渲染）
  - review-page（**即将被本变更重构**）：第 4 导航页「复习」= 到期分组列表 +
    方向卡会话 + 时间安排区块；API：`pull.include_ids`、
    `feedback.direction`、`queries.review_overview`、`/calendar` 端点
  - practice 写入状态映射修复（`schedule.recorded_status`：correct→reviewing、
    skip 零写入；fixtures 补了 CHECK）
- 本变更 **不做实现**，只交付规划产物；实现由你（下一个对话）执行。

## 二、要做什么（方案一，所有者已拍板）

一句话：**导航回三页，到期提醒与今日计划合流为练习页的一张「今天」列表，
时间安排移到练习页与学习安排并列，方向卡降为模式内可选轻会话。**

完整规格：`openspec/changes/consolidate-practice-views/`（proposal /
design / specs deltas / tasks）。设计要点：

1. 合流列表 = 计划行 ∪ 到期行，去重；行 = `名称 · 人话原因 · 动作`；
   原因短语规则见 design.md D2（覆盖仍低 / 拖了 N 天 / 上次没记住；
   零调度参数）。
2. 时间安排（月历 + 14 天柱状 + 重日预填）从复习页**原样搬移**到练习页
   学习安排旁（宽屏双栏，窄屏纵向）；`/calendar` 端点不动。
3. 卡片轻会话：开始闪卡/判断模式时若范围内有到期方向行 → 提示条
   「先翻 N 张到期卡」→ 原地卡片流（正面/揭示/1–5/feedback direction）
   → 回模式流程；拒绝则直接常规拉题，本次不再提示。
4. 拆除：review 导航项、`review_page`/`_send_page` review 分支、
   到期日期分组列表、复习页时间区块。

**保留不动**：`pull.include_ids`（400 with mode all）、
`feedback.direction`（只影响 schedule 键）、`queries.review_overview`
（合流列表数据源）、`/calendar`、micro quiz 全部、fixtures 的 CHECK 约束。

## 三、已知的坑（前几个对话的真实教训）

1. **tests/workbench/fixtures.py 的表结构必须与 pool_schema.py 一致**
   （problem_attempts 的 CHECK 教训）：fixture 缺约束 → 测试全绿但真实库崩。
2. **练习页选区键是 `wb_kp_selection_{ws}`**（saveSelectedKpIds），
   不是旧的 `wb_kps_`——手写交接逻辑时别用错（已因此修过一个 bug）。
3. **3091/3082 端口可能有残留的旧代码服务器进程**（TaskStop 杀不干净），
   走查前先 `netstat -ano | grep :308` 核对，必要时 taskkill。
4. **真实学习数据零写入**：走查一律用 scratch 副本
   （`cp pool/dmath.db` + `LESSONKIT_WB_HOME` 隔离注册表 + 独立端口），
   种子数据用相对今天的天数偏移（跨午夜会翻车，见 5）。
5. **同主键 INSERT OR REPLACE 会静默互相覆盖**（方向行种子踩过）。
6. **测试追加到文件末尾时注意 `if __name__ == "__main__":` 块**——
   追加在其后会让用例不被收集（计数对不上先查这个）。
7. Date.today() 跨午夜：长会话跨天时种子/断言里的「今天」会漂。
8. gh CLI 未安装：GitHub 操作走 REST API，凭据用
   `git credential fill`（token 只在内存用，不落日志）；合并用
   **PUT** `/pulls/{n}/merge`（不是 POST），`merge_method: "rebase"`。
9. 合并后等 CI：轮询
   `GET /repos/Amazinnn/Lesson-Kit/commits/{sha}/check-runs` 到全 completed。

## 四、验证关卡（缺一不可）

1. `python -m pytest tests -q` 全绿（基线 311+）
2. `node --test tests/workbench/*.test.js` 全绿（基线 72+）
3. `openspec validate --specs --strict` 全过（基线 10 个规格）
4. scratch 走查：种子 49 条调度 + 2 目标 → 三页导航、合流列表排序与原因
   短语、卡片轻会话全程、时间视图并列布局；**截图自检清单**：
   主行动唯一 / 令牌统一 / 行对齐 / ≤2 点击 / 空状态一句话一个动作
5. PR rebase 合并后 main CI 绿

## 五、验收标准（所有者特别强调）

**测试通过 ≠ 完成。** 实现效果必须简洁美观、流程清晰：练习页首屏应能
一眼回答「今天做什么」，合流列表行不超过两种徽标，复习相关一切以
「可以复习」的提醒语气出现（绝不强迫、绝不露参数）。走查发现的别扭点
当场修或记入 UX 清单（现有清单见交付讨论：图谱标签重叠、练习会话
不聚焦、禁用主按钮样式、40 字截断无省略号）。

## 六、收尾

- 归档变更（`openspec/changes/archive/2026-MM-DD-consolidate-practice-views/`）；
- `workbench-ui` spec 的 Purpose 段改写为三页导航（归档时必做）；
- changelog 落档；同步检查 REQUIREMENTS / DISCUSSION-RECORD /
  FUTURE-NOTES / ARCHITECTURE 四处与新状态一致。
