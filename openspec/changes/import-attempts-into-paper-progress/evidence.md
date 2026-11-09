# 6.5 隔离临时工作区真实验收（真实 CLI + 真实浏览器）

日期：2026-11-09。环境：`LESSONKIT_WB_HOME=%TEMP%\ia-accept\home`，工作区 `ia-accept`（`%TEMP%\ia-accept\ws`，course `ia`），daemon 3221。运行时身份：`/api/runtime` = `source_root: D:\Projects\Academic Workflow\lesson-kit`（主检出本分支），editable 安装经中性 cwd 探针 = 主检出。截图：`.playwright-mcp/ia-accept-saved-papers.png`、`.playwright-mcp/ia-accept-parked-paper-c.png`（工作区内，未含敏感信息）。真实 22 工作区与 `%TEMP%\wb64` 均未触碰。

## A. 创建并保存 Paper（真实 CLI）

- 受治理内容路径建题库：`lesson-kit ingest ia-accept bundle --input bundle.json --apply`（check → apply，零拒绝），1 知识点 + 3 题（`ia-ch01-prob-001..003`，均带 `source_evidence`）。
- `lesson-kit papers ia-accept save`：ps-001（3 题）、ps-002（2 题）；后续 E 步再建 ps-003（2 题）。

## B. check / apply（真实 CLI，DB 全表快照对照）

- check（`paper_id=ps-001`，2 条纸上作答）：exit 0、`writes=0`、预览 mode=new / progress_after 2/3；**24 张表逐行快照 diff = 空集**（零写入）。
- apply（同 manifest）：exit 0，attempt ids [1,2]；写入 = `problem_attempts` 0→2、`attempt_operations` 0→2、`paper_state.checkpoint_json`（on_submit 检查点）+ `practice_execution_ids` 1 行；`feedback_events/learner_signals/problem_progress/learning_current_state/review_schedule/practice_runs/active_practice` **全部零变化**——无 rating 导入只动 Paper 执行进度。

## C. 浏览器打开同一 Paper（Playwright，daemon 3221）

- 已存试卷列表显示「ia 验收卷 A：3 题 · 已完成 2/3」，入口为「继续练习」（导入进度被卷读取识别）。
- 打开后执行被恢复为活动执行（cursor 在唯一 pending 项），第 1、2 题显示「已提交」+ 导入答案原文；刷新页面再进，状态照旧恢复。
- 浏览器继续作答第 3 题（综合题小问）：新 attempt id=3（`ia-ch01-prob-003`），前两题保留导入 attempt 1/2 不被覆盖。
- 交卷：`提交试卷` 后 `practice_runs` 落 1 条 completed（source_ref=ps-001、execution_id=1），active 清空，归档 items 带 attempt 链接 [1,2,3]，3 条 attempt 全部保留。

## D. 活动卷 vs 停放卷（真实 CLI + 浏览器）

- ps-003 经导入建成停放检查点（1/2）；浏览器启动 ps-002 为当前活动卷并答出 1 题（attempt id=5，active execution 3，items [(0,stuck),(1,pending)]，cursor 0——逐行快照）。
- 活动卷进行中，对停放 ps-003 再导入（attempt id=6）：apply exit 0、mode=parked、progress 2/2；**活动卷 active 行与 items 快照逐字段不变**、cursor 不变、attempt 数 5→6 只新增目标卷那条。

## E. 受治理补题 → append → 再导入（真实 CLI）

- 补题：`ingest bundle --apply` 建 `ia-ch01-prob-004`（同一 KP、source_evidence；第二次 apply 被既有可恢复备份挡下，移开备份后成功——防覆盖设计如实记录）。
- `papers append ps-003 --problem ia-ch01-prob-004`：position=2 追加、旧两项 answered(4/6) 保留、新项 pending；checkpoint paper_generation 1→2 与 state 一致。重复调用：`already_present`、progress 不变（幂等零写）。
- 再导入补题答案：exit 0、progress 3/3、新 attempt id=7、旧两项 attempt 仍为 4/6、题序不变。
- 相同 manifest 重放：exit 0、attempt id 与 paper 段完全一致、`problem_attempts` 仍 7 条（幂等重放零重复写）。

## F. 最终状态

- ps-001：已交卷归档（run 1 completed），3 attempt 在历史可读。
- ps-002：活动执行（1/2），未受任何导入影响。
- ps-003：停放检查点 3/3（含补题），读取一致（截图 2）。

## G. 拒绝场景零残留（真实 CLI，全表快照）

| 场景 | exit | 错误 | 表变化 |
|---|---|---|---|
| 未知 Paper（ps-999） | 2 | `unknown Paper: ps-999` | 无 |
| 非成员题（prob-001 不在 ps-003） | 2 | `problem is not part of this Paper` | 无 |
| 批次后段非成员（卷内题+卷外题） | 2 | 同上（整批拒） | 无（attempts 仍 7、operations 仍 5） |

批次整体性另有 pytest 故障注入证据（第二个 `_record` 失败 → 第一批 attempt/operation/进度全部回滚，见 test_attempts.py::test_a_failed_later_item_rolls_back_the_whole_batch）。

## Agent 部分

注入提示词与三主题契约文本由 `tests/workbench/test_agent_contracts.py`（11 passed）钉住：`paper_id` 顶层可选与绑定三模式、无 rating 只动执行进度、重绑保留旧 attempt、legacy 可归档/显式模式等交卷、三步补题（建内容→append→导入）、显式意图门槛（讨论不写入）、`_prompt` 的纸面导入规则。未调用真实 LLM（本包不要求）。
