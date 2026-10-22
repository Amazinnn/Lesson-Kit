# IMPL-W3d — `middle-navigation.js`：客户端换页 · 骨架屏容器 · 焦点不抢

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 21 组（21.1 / 21.3 / 21.5）**。
> **只改 `workbench/server/static/middle-navigation.js` 这一个文件。**

## 前置（自己核实，不要相信任何人的口头汇报）
- 六个实现 agent 与你**同时在跑**，别人正在改 `workbench.js` / `pages.py` /
  `practice-flow.js` / `paper-practice.js` / `records.py` / `workbench.css`。
  **你只碰 `middle-navigation.js`。**
- CSS 侧已落 `#middle-page > *` 的容器动画与 `lk-skeleton-sweep` 关键帧 ——
  **先 grep `workbench.css` 确认类名与结构**，不要凭猜。

## 硬约束
- **只改 `workbench/server/static/middle-navigation.js`**。不碰 `workbench.css` /
  `workbench.js` / `pages.py` / `practice-flow.js` / `paper-practice.js` / `records.py` /
  `app.py` / `docs/` / `openspec/`。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **现有所有交互逻辑一个字都不许改**（所有者绝对底线）：
  换页流程、请求序列、URL / 历史记录行为、Agent 右栏**保持挂载**（同工作区中栏导航
  不得重建 `#ai-column`、不得丢滚动位置与草稿输入）一律不动。
- **不得给子元素加一次性动效类名**（21.5 的硬约束）——
  切页会整体替换 `#middle-page` 的 innerHTML，类名会被冲掉。
  **验证：`grep -n "classList.add" middle-navigation.js` 不得出现一次性动效类名。**
- 知识图谱：`middle-navigation.js` 里**与图谱相关的代码一行都不许碰**。
  ⚠️ 图谱页的 `#middle-page` 是**全站共用容器** ⇒ 转场作用域**必须排除图谱页**
  （CSS 侧已用 `#layout:not([data-page="graph"])` 排除，**你不要在 JS 侧再实现一遍**，
  也不要让图谱页播放上浮淡入）。

## 必读
1. `tasks.md` 的 **第 21 组全文**
2. `design-notes/motion-spec.md` §7.1（**终态铁律**：静态样式 = 终态，
   起始态只写在 `@keyframes` 内部）
3. `design-notes/walkthrough-harness.md`（走查执行器：请求序列捕获器、
   池副本 + 隔离注册表 + 独立端口，**永不写真实池**）
4. `decisions.md` 的 **A-2**（动效偏好优先级）· **A-27 M-D / M-E** · **A-39**（服务陈旧副本）
5. `design-notes/graph-isolation.md` **F-6**（转场排除图谱页）

## 要做什么

### 21.1 骨架屏 = 灰块 + 微光扫过
- 容器切页**前**呈骨架（`#middle-page` 先呈骨架状态），内容到位后**由容器动画接管**。
- 加载态带 **`aria-busy`**（置位与复位都要正确）。
- **不引 spinner 图标资源**（无新资源文件）。

### 21.3 焦点不被抢走
- 转场与浮层出现时**不得**抢焦点。
- 装饰层一律 **`pointer-events: none`**，可交互元素**不在**装饰层内。
- 切页后焦点仍在原处，或落到新页首个可交互元素（**按既有行为**，
  不要改变现有焦点顺序）。

### 21.5 容器级转场的实现约束落地
- 转场**必须是 `#middle-page` 自身的 animation**（CSS 侧已实现）——
  **你不需要在 JS 里做任何动效**。
  你的工作是**保证容器结构满足 CSS 的选择器要求**：
  `#middle-page > *` 挂得上、`#middle-page` 本身能承载骨架态。
- **不含 `scale`**：`scale` 会改变 `graphCanvas.getBoundingClientRect()`，
  导致环境色 canvas 与真实画布错位。
- 骨架屏同样挂容器（`#middle-page` 先呈骨架、内容到位后由容器动画接管）。

### 21.6 降级下骨架与内容的终态一致
- reduced-motion 或动效偏好关时：骨架**不扫光**、内容**直接以终态出现**。
- **不得**停在「骨架永久停留」或「内容半透明」。
- `aria-busy` 在降级下同样正确置位与复位。
- 动效偏好读取用**既有的** `window.lkMotion.mode()` —— **复用它，不要另建一套**。

## 验证
- 跑 AGENTS.md 四条验证命令：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- 截图走查：练习 ⇄ 知识点 ⇄ 记录三次客户端换页的**中间帧** + 各自的 reduced-motion 降级对照帧
  （**终态一致**）。
- **图谱页必须逐像素零变化**（G-5 否定式断言）——
  特别验证：**进入图谱页不播放上浮淡入**。
- 走查服务必须：**仓库根为 cwd + 独立端口（不要 3081）+ 池副本 + 隔离注册表**；
  启动前先比对 `curl -s http://127.0.0.1:<端口>/static/workbench.css | wc -c` 与
  `wc -c workbench/server/static/workbench.css`（A-39：两个数必须相等）。

## 落盘纪律与回报
- **小步提交**：每完成一块（骨架 / 焦点 / 降级）**单独 commit**。
  **不要 `git add -A`** —— 只 add `middle-navigation.js`。
- 若文件里出现**你没写过的改动**：先 `git diff` 看清楚再决定，**不要静默覆盖**。
- 最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **每个 commit 的内容** +
  **`aria-busy` 的置位 / 复位代码位置** + **降级分支的判定写法** +
  **「没有一次性动效类名」的 grep 证据** + 四条验证命令结果 + **待裁决项**。
- 数字、文件行数、task id 一律以**当场跑出来的命令输出**为准。
