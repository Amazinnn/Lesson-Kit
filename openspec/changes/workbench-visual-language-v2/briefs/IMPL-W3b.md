# IMPL-W3b — `pages.py`：练习页 / 知识点页 / 试卷页 / 设置视图的服务端侧

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的
> **第 15 组（15.x 的服务端侧）** · **第 16 组（16.1–16.3 / 16.5 / 16.7）** ·
> **第 18 组（18.2 / 18.4 / 18.5）** · **第 21 组的服务端侧（21.2 的三态组件）** ·
> **6.2 / 6.3 中属于 `pages.py` 的挂载点**。
> **只改 `workbench/server/pages.py` 这一个文件。**

## 前置（自己核实，不要相信任何人的口头汇报）
1. `workbench.css` 已被别的 agent 改过（阅读层 `.wb-reading` + 动效 token）。
   你的服务端侧要**挂对类名**，但**不要去改 CSS**。
2. 六个实现 agent 与你**同时在跑**，别人正在改 `workbench.js` / `practice-flow.js` /
   `paper-practice.js` / `middle-navigation.js` / `records.py` / `workbench.css`。
   **你只碰 `pages.py`。**

## 硬约束
- **只改 `workbench/server/pages.py`**。不碰 `workbench.css` / `workbench.js` /
  `practice-flow.js` / `paper-practice.js` / `middle-navigation.js` / `records.py` /
  `app.py` / `pool/` / `docs/` / `openspec/`。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **现有所有交互逻辑一个字都不许改**（所有者绝对底线）：
  请求序列、载荷键、DOM 身份、滚动位置、焦点行为、既有行为偏好（左栏「运行中发送方式」
  「练习显示自评」两���**留在左栏原位**，不得搬走）一律不动。
- 知识图谱：`pages.py` 里**与图谱相关的代码一行都不许碰**（含 `graph` 字样的函数与分支）。
- **零新增请求、零池写入**：任何统计必须走**现成读路径**。

## 必读
1. `tasks.md` 的 **第 15 / 16 / 18 / 21 组** 与 **6.2 / 6.3**
2. `design-notes/layout-spec.md`（三栏几何、标志带、中栏版式、密度分区）
3. `design-notes/component-spec.md`（题面纸 / 解析纸 / 作答块 / 题号格 / 分组卡片 / 计数条 / 空态）
4. `docs/PRODUCT-MANUAL.md` §3.2 知识点页（**单侧结构线 2px 是硬性要求**）
5. `docs/GLOSSARY.md`「当前学习状态」条（`needs_work` 重点练习 / `review` 可以复习 /
   `mastered` 掌握）与「行动提醒」条（**逐条提醒只用前两个，其余保持中性**）
6. `decisions.md` 的 **A-11**（主题默认来源）· **A-23**（沉底不是深色块）· **A-27 M-F/M-G**
   · **A-29**（里程碑只有两个条件）· **A-38** · **A-41**（`.rich-text` 迁移口径）

## A. 6.2 / 6.3 的 `pages.py` 挂载点迁移
- 把 `pages.py` 里挂 `class='rich-text'` 的四处改成 `class='wb-reading'`：
  题面（`#paper-question`）、解析（`#paper-reference`）、关联题（两处 `linked-problem-text`）。
- **只改类名，不改内容、不改结构、不改顺序。**
- ⚠️ **`.rich-text` 的 CSS 规则本轮不由你删**（CSS 侧另一个 agent 在动同一个文件，
  另有三个 agent 也在改别的文件里的挂载点）⇒ 本轮 `pages.py` 里 `rich-text` 归零，
  全仓还不归零，**这是预期状态**（口径见 `decisions.md` **A-41**）。
- 题面变体：题面与解析挂 `wb-reading wb-reading--stem`（`.wb-reading--stem` 由 CSS 侧提供，
  **若 grep 发现 CSS 侧还没有这个类，就只挂 `wb-reading` 并在回报里说明**）。

## B. 第 16 组 · 练习页版式（服务端侧）
- **16.1** 题面 `#paper-question` 从「卡片内段落」改为**一张独立的纸**（比卡片更亮一级
  + 淡结构线）；**24px 大号题号**（像书的章节号）；题面**不做装饰性阴影强调**。
- **16.2** 解析 `#paper-reference` 改为**与题面同级**的另一张纸（不再是灰掉的小脚注），
  只用小标题区隔。
- **16.3** 作答区 `#paper-answer` 前加淡结构线 + 「你的作答」标签 + **沉底块**
  `--surface-sunken`（**不是近黑墨块**；A-23：浅底深字）；
  题面内的非 stem 文字（来源行与作答标签）**降一档到 16px**，stem 保持阅读字号。
- **16.5** setup 区（`#paper-setup`）、完成页（`#paper-completion`）、
  时间安排（`#practice-planning` + `_daily_plan`）统一到新卡片规格；
  时间安排降级为**可展开的次级信息**。
- **16.7** 完成页**预留三处承载位**（给第 8/17 组的动效用）：
  ① 统计数字槽位；② 进度带（`.lk-progress` + `.lk-progress__fill`，
  `transform-origin: left center`，只动 `scaleX`）；③ 里程碑锚点容器
  （`pointer-events: none`，**不得覆盖完成页 CTA**）。
  ⚠️ **承载位的静态样式必须等于其终态** —— 数字直接显示最终值、进度带静态满格、
  爆点与纸片静态不出现；**起始态只写在 CSS 的 `@keyframes` 内部**。

## C. 第 18 组 · 知识点页（服务端侧）
- **18.2** `state_labels`（现「重点练习 / 可以复习」文字标签）改为**彩色圆点**：
  颜色主通道 + 几何冗余通道，**零可见文字**，圆点带 `aria-label` / `title`。
- **18.4** 列表空态改**插画 + 一句 + 满宽主按钮**（按钮文案即动作）；关联题目卡统一卡片规格。
- **18.5** 章节内**计数条**（不是新卡片、不是百分比）：本章节知识点**总数** +
  处于 `needs_work` / `review` / `mastered` 三态的**个数**。
  数据源**只用现成读路径**：总数取 `pool.kps(prefix)`，
  各态计数取 `learning_current_state.state`（`workbench/data/pool.py` 里已有）——
  **不新增统计行、不写池、不改请求序列**。
  文案用 GLOSSARY 已定义的状态名。
  ⚠️ **不得**出现正确率 / 掌握度 / 完成度百分比（GLOSSARY `_Avoid_`）；
  ⚠️ **不得**在顶栏章节透镜里显示任何每章计数（现行 spec 明令）。
  ⚠️ 该计数条是**状态分布的汇总**，不是逐条的行动提醒 —— 逐条提醒仍只用
  「重点练习 / 可以复习」，其余保持中性（这个区别要写进 `docs/PRODUCT-MANUAL.md` §3.2 / §7.4，
  **但不要改 docs/** —— 把它列进回报的「待同步文档」清单，由主会话统一改）。

## D. 第 15 组 · 左栏导航语法（服务端侧）+ 第 21 组服务端侧
- 左栏**只承载行为偏好**（既有两项留在原位）+ 外观偏好入口（设置视图开关已由第 11 组落地，
  **不要重复实现**）。
- **21.2** 空态 / 加载态 / 错误态**三态各有组件**：`.empty-state`（插画 + 一句 + 满宽主按钮）、
  `.skeleton`、错误块；错误态用红色，且**红色仅用于失败与阻塞**。
  错误态与空态**各有可触发路径**。

## 验证
- 每完成一块就跑 AGENTS.md 四条验证命令：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- `tests/workbench/` 下的路由测试可能断言了**旧的字面量**（类名 / CSS 片段）。
  若因你改了类名而失败：**改测试的断言**（这属于契约同步，允许），但**只改与你改动相关的断言**。
- 截图走查：练习全流程（setup → 题面 → 作答 → 解析 → 自评 → 完成页）+ 知识点列表与详情。
  **图谱页必须逐像素零变化**（G-5）。

## 落盘纪律与回报
- **小步提交**：每完成一块（迁移 / 练习页 / 知识点页 / 三态组件）**单独 commit**。
  **不要 `git add -A`** —— 只 add `workbench/server/pages.py`（必要时加你自己的测试文件）。
- 若 `pages.py` 里出现**你没写过的改动**：先 `git diff` 看清楚再决定，**不要静默覆盖**。
- 最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **每个 commit 的内容** +
  **新增/改动的 HTML 结构（贴片段）** + **18.5 计数条的数据来源（贴代码）** +
  **16.7 三处承载位的实际类名** + **改了哪些测试断言** + 四条验证命令结果 +
  **待同步文档清单** + **待裁决项**。
- 数字、文件行数、task id 一律以**当场跑出来的命令输出**为准。
