# practice-loop-ux-completion 提案

## Why

FUTURE-DEVELOPMENT-NOTES 记录的 4 条 UX 遗留（图谱标签重叠/挤压、近期活动
40 字截断无省略号、日历格内目标 chip 只显示首字、统一自评下微题即时判分被
立即翻页覆盖），加上两条走查/规格核对中发现的结构性缺口：

1. **batch 模式的判分语义**（所有者 2026-08-29 拍板）：统一自评下判分即时、
   自评延迟——micro/yes_no 答完立刻见对错横幅（答错高亮正确项），短暂停留后
   自动翻页；batch 的价值 = 练习中不打断节奏，而非延迟判分。现状是横幅被
   `loadNext()` 的 innerHTML 替换瞬间吞掉，对错只能等收束页。
2. **闪卡会话模型**（所有者拍板）：闪卡支持自由前后翻页——操作模型为
   「历史回翻 + 前进拉新」：翻回看已揭示的卡（状态保留），到历史末尾再按
   下一张才拉新卡；结束路径不变。
3. **ai-teacher-bridge 的 UI 履约缺口**：spec 既有条款要求 explain 结果与
   失败原因 "shown in the UI"，后端 `POST /ai/{operation}` 与 job 轮询齐备，
   但练习页没有「讲解」「诊断」入口。本变更补齐前端，使手册第 8 章可如实
   成文。
4. **标签完整显示**（所有者拍板）：任何界面一律完整显示文本，不截断、不加
   省略号；名称过长属命名纪律问题，UI 不做兜底。图谱标签重叠由标签感知的
   碰撞间距与折行解决（库内已有 `editable-graph` 先例）。

## What Changes

- 前端练习流立「会话牌组」脊柱（新静态模块 `practice-deck.js`，纯逻辑无
  DOM）：历史 + 游标 + 每项视图状态（作答/选项/判分/揭示/自评态），统一
  渲染入口 `renderDeckItem`，刷新恢复升级为恢复游标与全部视图状态。
  存储格式 SESSION_KEY v2（`{v:2, items, cursor}`），session-end 读同一
  items，外部结构不变。
- batch 模式：判分横幅（对/错 + error reason，答错高亮正确选项）停留
  `VERDICT_HOLD_MS = 2000` 后自动推进；exam 文本题无判分不停留；横幅纯本地
  展示，不写任何学习记录（与 workbench-ui "Unified rating" 条款一致）。
- 闪卡两种自评模式下提供「上一张/下一张」；immediate 已评卡回看只读；
  未揭示的跳过卡回看后可补揭示（skipped→unrated）；exclude_ids 仍取全部
  历史；耗尽/提前结束/收束路径不变。
- 练习页 problem 项（非闪卡）加「讲解」「诊断」一键任务入口：讲解
  `POST /ai/explain {problem_id}`；诊断附当前作答 `user_answer`（未作答软
  门槛提示）；轮询 `GET /ai/jobs/{id}` 显示状态，done 后 `GET /explain/`
  取结果按分节 markdown 渲染于练习栏，failed 显示原因；无 provider 时按钮
  不可用而非报错。note/stuck_step 本期不开 UI 入口（API 已支持）。
- 标签完整显示：图谱标签纳入碰撞尺寸 + 多行折行（移植 editable-graph
  先例）；近期活动去 `[:40]` 截断；日历 goal chip 改自动折行、格高自适应。

## Capabilities

### Modified Capabilities

- `micro-quiz-content`：Type-aware practice rendering 补 batch 模式判分停留
  与正确项高亮。
- `flash-card`：Flash card practice mode 补会话历史回翻条款。
- `ai-teacher-bridge`：新增练习页一键任务入口条款（既有 "shown in the UI"
  的前端履约）。
- `workbench-ui`：Living graph motion and readable labels 补标签完整显示与
  折行；新增跨表面完整显示条款（近期活动、日历 chip）。

## Impact

代码：`workbench/server/static/practice-deck.js`（新）、`workbench.js`
（练习段接入牌组）、`workbench.css`（标签/横幅/导航样式）、
`workbench/server/pages.py`（脚本引入与练习操作区按钮）、
`workbench/data/queries.py`（去截断）、`workbench/server/static/graph-physics.js`
（碰撞半径纳入标签尺寸，表现层）。兼容边界：immediate 模式流程、
`/pull`、`/pull-cards`、`/feedback` 写入语义、session-end 页面结构均不变；
用户可感知变化仅限本变更批准的四项。冻结边界说明：图谱投影管线（ingest/
投影算法）不动，仅改运行时表现层布局（库内有 editable-graph 标签感知碰撞
先例）；若走查发现布局退化，回退为纯标签层避让。GLOSSARY / PRODUCT-MANUAL
（6.x 增补与 8 章成文）随后续 docs PR 同步。
