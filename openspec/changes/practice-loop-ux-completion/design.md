# practice-loop-ux-completion 设计

## 两条通道

需求的载体是练习前端，现状是单向流 + `innerHTML` 整体替换 + 模式 `if` 分叉。
逐项贴补丁会碎，因此实现收敛为两条通道：

1. **通道一（会话牌组脊柱）**：判分横幅、闪卡回翻、讲解/诊断上下文三个
   行为都依赖「历史 + 游标 + 每项状态」，先立这一层，三个行为成为其上的
   薄 UI。
2. **通道二（完整显示清扫）**：标签完整显示与牌组无关，独立一遍扫过
   图谱 / 近期活动 / 日历 chip 三个表面。

## practice-deck.js（纯逻辑，无 DOM）

参照 `graph-physics.js` 先例：独立静态文件、IIFE 挂全局、node 可单测
（`tests/workbench/practice_deck.test.js`）。

- 状态：`{items, cursor}`；每项 `{id, kind: "problem"|"card", payload,
  answer_text, choices, verdict, revealed, state}`。`state` 沿用现行
  `active | unrated | rated | skipped` 语义。
- 接口：`append(deck, item)`（仅历史末尾追加，游标随尾）、`current(deck)`、
  `atEnd(deck)`、`goTo(deck, index)`、`settle(deck, id, patch)`（按 id 合并
  字段）、`serialize(deck)` / `deserialize(data)`。
- 序列化：SESSION_KEY 存 `{v:2, items, cursor}`；items 字段名沿用现行
  `problem_id / state / answer_text / card / front / back`（session-end 页与
  恢复逻辑的兼容面）。旧数组格式（v1）读取时游标取末项，单向兼容。
- `workbench.js` 里的 `session()` / `updateSession()` / `setCurrent()` 改为
  牌组之上的薄适配；session-end 过滤 `state === "unrated"` 不变。

## 推进策略（A：判分横幅）

- `submitAnswer`（graded 且 batch）：`settle {choices, verdict}` → 由状态
  渲染横幅（对/错 + error reason；答错高亮正确选项，选项禁用）→
  `setTimeout(advance, VERDICT_HOLD_MS)`，常量 2000ms。
- generation token：每次会话事件（开始/结束/手动导航）递增；定时器回调
  校验 token，防止停留期间用户结束会话后被迟到的翻页击穿。
- exam 文本题 batch：无本地判分，不停留，直接推进（同今）。
- immediate：流程不变（判分 + 自评按钮）。
- 横幅不写库：batch 下 `state` 仍为 `unrated`，feedback 仍只在收束页写。

## 闪卡回翻（B：牌组导航）

- flash_card 模式（两种自评）在操作区显示「上一张/下一张」。
- `advance()` = `atEnd ? 拉新（pull-cards，exclude= 全部 items 的 id） :
  goTo(cursor+1) + 渲染`；「上一张」= `goTo(cursor-1)`，游标 0 处禁用。
- 回看渲染由 `renderDeckItem(item)` 状态驱动：已揭示显背面；batch 下已
  揭示卡保持 unrated 标记；immediate 已评卡回看只读（显示已评状态，不再
  提交）；未揭示的跳过卡回看后可补揭示，揭示即 skipped→unrated。
- 耗尽（拉新返回空）、提前结束、session-end 收束路径全部不变。

## 讲解/诊断入口（C：牌组当前项 = 上下文）

- 入口：练习操作区（problem 项显示，卡片项不显示——`/ai/{operation}` 以
  problem_id 为键，卡片不是 problem）。
- 讲解：`POST /ai/explain {problem_id}` → `{job_id}` → 轮询
  `GET /ai/jobs/{job_id}`（350ms 节奏，与对话轮询一致）→ done 后
  `GET /explain/{problem_id}` 取 markdown，渲染在练习栏 composer 下方
  （复用 `richText`/markdown 渲染与 KaTeX）；failed 显示原因。
- 诊断：同上，body 附 `user_answer = 当前项 answer_text`；未作答时软门槛
  提示「请先作答再诊断」，不发起请求。
- 降级：providers 列表为空或加载失败 → 按钮禁用 + title「暂无可用 Agent」
  （与既有降级文案一致）。
- 任务级停止路由不存在（仅会话级 cancel），UI 只显示运行状态；结果文件
  持久于 `.lessonkit/explain/`，按钮可重复查看既有结果。

## 标签完整显示（D）

- 图谱：`graph-physics.js` 碰撞半径纳入标签占位（移植
  `frontend/editable-graph/src/main.js` 的 label-aware 半径与折行逻辑）；
  `workbench.css` `.graph-node-label` 去固定 max-width 改折行。
- 近期活动：删 `queries.py _item_label` 的 `[:40]`，条目折行完整显示。
- 日历：`.calendar-goal` 去 nowrap/ellipsis 改折行，格高自适应。
- 冻结边界：不动投影管线；走查见布局退化则回退纯标签层避让（标签错位
  而非节点重排）。

## 不做的事

- 不加构建步骤、不引框架、不加 hover 省略（所有者禁省略号）。
- 不动 immediate 模式交互、不动 `/pull` `/pull-cards` `/feedback` 契约、
  不动 session-end 页面结构。
- 不做任务级 job cancel、不开 note/stuck_step 的 UI 入口。
