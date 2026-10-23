# IMPL-W3a — `workbench.js`：三栏几何 JS 侧 · 阅读层挂载点迁移 · 动效 JS 编排

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的
> **第 13 组 JS 侧（13.x 的 JS 部分）** · **6.2 / 6.3 中属于 `workbench.js` 的挂载点** ·
> **8.4 / 8.7JS / 8.8 的 JS 编排**。
> **只改 `workbench/server/static/workbench.js` 这一个文件。**

## 前置（自己核实，不要相信任何人的口头汇报）
1. `workbench.css` 已被前一个 agent 改过（阅读层 `.wb-reading` + 动效 token + 分级降级闸门）。
   **动手前先读 `workbench.css` 现状**，确认 `.wb-reading` 规则已存在、动效 token 已在位。
2. 六个实现 agent 与你**同时在跑**，别人正在改 `pages.py` / `practice-flow.js` /
   `paper-practice.js` / `middle-navigation.js` / `records.py` / `workbench.css`。
   **你只碰 `workbench.js`。**

## 硬约束
- **只改 `workbench/server/static/workbench.js`**。不碰 `workbench.css` / `pages.py` /
  `practice-flow.js` / `paper-practice.js` / `middle-navigation.js` / `records.py` /
  `app.py` / `docs/` / `openspec/`。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **现有所有交互逻辑一个字都不许改**（所有者绝对底线）：
  请求序列、载荷键、DOM 身份、滚动位置、草稿输入、焦点行为、按钮位置与含义一律不动。
  本轮只做「几何变量写法」「类名迁移」「动效编排」「新增只读能力」。
- 知识图谱：`workbench.js` 里**与图谱相关的代码一行都不许碰**（含 `graph` 字样的函数、
  图谱页专属分支、图谱数据请求）。图谱的节点重设计归 `graph-node-visual-language` change。
- 无框架 / 无构建 / 无 npm / 无 CDN / 无第三方库（数字滚动用 vanilla rAF）。

## 必读
1. `tasks.md` 的 **第 13 组**、**6.2 / 6.3**、**8.4 / 8.7 / 8.8**
2. `design-notes/motion-spec.md`（**你的 @keyframes 与交互映射的规格书**：§3 关键帧、
   §4 交互映射、§6 参数化输入表、§7.1「起始态只写在 @keyframes 内」的终态铁律）
3. `design-notes/component-spec.md`（连对计数器 / 横幅 / 火苗簇 / 完成页承载位的组件形态）
4. `decisions.md` 的 **A-2**（动效偏好优先级）· **A-27 M-D…M-N**（动效清单）
   · **A-29**（里程碑只有两个条件）· **A-38**（跨组对齐：偏好字段名 `sound`、
   庆祝爆点元素必须带 `lk-celebrate-burst` 或 `data-lk-cue="milestone"`）· **A-41**（`.rich-text` 迁移口径）
5. `decisions.md` 的 **A-39**（视觉验证前先确认服务的是当前工作区）

## A. 三栏几何的 JS 侧（13 组）
现状：`workbench.css` 里的 `grid-template-columns: minmax(0,1fr)` **从不生效** ——
被 `workbench.js` 每次 inline 覆盖成 `minmax(420px,1fr)`。改法：
- 改成写**两个 CSS 变量**：`setProperty("--wb-col-left", …)` / `setProperty("--wb-col-right", …)`
  （变量名以 CSS 侧实际落地的名字为准 —— **先 grep `workbench.css` 确认**，
  变量写在 `#layout` 上，不在 `:root`）。
- 保留中栏 **≥420px** 的夹取规则；拖拽结束时清掉 inline 覆盖，让 CSS 模板接管。
- **不改变任何拖拽行为语义**：起手位置、吸附、持久化、键盘操作一律不变。
  这是「写法迁移」，不是「行为改写」。
- 三个 token **禁止合并**：`--shell-measure`（880px 阅读轨宽）≠ `--measure`（38em 行长）
  ≠ `--shell-col-left` / `--shell-col-right`（A-20-1 / A-21）。

## B. 6.2 / 6.3 的 `workbench.js` 挂载点迁移
- 把 `workbench.js` 里两处 `<div class='rich-text'>` 挂载改成 `<div class='wb-reading'>`。
- **只改类名，不改内容、不改结构、不改顺序。**
- ⚠️ **`.rich-text` 的 CSS 规则本轮不由你删**（CSS 侧另一个 agent 在动同一个文件，
  且另有三个 agent 也在改别的文件里的挂载点）⇒ **本轮 `workbench.js` 里 `rich-text` 归零，
  但全仓还不归零**，这是预期状态。
- 口径见 `decisions.md` **A-41**（段二：CSS 段已落，HTML 段分文件推进，
  规则删除留到所有挂载点都迁完之后的那一波）。

## C. 8.4 / 8.7 / 8.8 的 JS 编排
- **8.4 三处 JS 编排**（**只动 `textContent` / 已有计数器的值与 class**）：
  ① 统计数字**滚动**（rAF 逐位滚动到目标值；不新增节点、不新增事件绑定）；
  ② **火苗**点亮（写已有装饰层元素的 class）；③ **进度带**（写已有进度条的值与 class）。
  ⇒ **不新增节点、不新增事件绑定、不新增请求、不改任何学习数据或持久化路径。**
- **8.7 台灯转场**：转场**开始时**（不是结束时）把**目标主题**的 `--surface-base`
  写进涟漪层的 CSS 变量（`--lk-ripple-base` 的**读取端**在 CSS 侧；
  写端在你这里）。晚一帧就会「旧色闪一帧」。
  ⚠️ 涟漪层是**底色层**（`z-index: 0`），**不得**接到会随主题变的卡面 token 上。
- **8.8 两档庆祝**：里程碑档在 **① 本轮全对** 或 **② 章节首次完成** 时启用；
  **只有这两个条件**（A-29 裁定：不得用任何代理指标近似，例如「比上次做得好」）。
  日常档（至少有一道错）**不挂**几何爆点与纸片。庆祝**全部在响应到达后触发**，
  **请求时序不得变**。
- ⚠️ **铁律：动效元素的静态样式必须等于它的终态** —— 起始态（`opacity: 0` / 位移 / 缩放）
  **只能写在 CSS 的 `@keyframes` 内部**。JS 只切 class，不写内联起始态。
- ⚠️ 庆祝爆点元素必须带 class `lk-celebrate-burst` 或 `data-lk-cue="milestone"`（A-38），
  否则音效与爆点不同拍。

## D. 主题 / 动效 / 声音偏好的读取（已有实现，只做加固）
- 三个偏好都在既有 `wb_settings_<工作区>` JSON 里（`SETTINGS_KEY`），
  字段名分别是 `theme` / 动效偏好 / **`sound`**（布尔，默认**开**）——
  **字段名必须是 `sound`**（A-38），不新增 localStorage 键、不落服务端、不写池。
- 动效偏好**默认跟随**系统 `prefers-reduced-motion`；**学习者显式选择优先于系统**（A-2）。
  四种组合都要成立：系统 reduce + 偏好未设 ⇒ 弱动效档；系统 reduce + 偏好显式开 ⇒ 覆盖系统恢复完整；
  系统允许 + 偏好未设 ⇒ 完整；系统允许 + 偏好显式关 ⇒ 全部直切。
  `window.lkMotion.mode()` 是既有入口 —— **复用它，不要另建一套**。

## 验证
- 每完成一块就跑 AGENTS.md 四条验证命令：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- **有 Node 的测试也要跑**（仓库里有 `tests/workbench/*.test.js`）——
  若有现成的 JS 测试命令就跑；没有就至少 `node --check workbench.js`。
- 截图走查：练习页 → 完成页 → 庆祝两档 → 降级对照帧；
  **图谱页必须逐像素零变化**（G-5 否定式断言）。

## 落盘纪律与回报
- **小步提交**：每完成一块（几何 / 迁移 / 编排 / 偏好）**单独 commit**，
  commit message 写清是哪块。**不要 `git add -A`** —— 只 add 你改的那个文件。
- 若 `workbench.js` 里出现**你没写过的改动**：那是别的 agent 越界了或上一步留下的，
  **先 `git diff` 看清楚**，再决定是否继续；**不要静默覆盖**。
- 最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **每个 commit 的内容** +
  **几何变量的最终写法（贴代码）** + **动效编排的落点清单（哪个事件 → 哪个 class）** +
  **里程碑两条件的判定代码在哪** + 四条验证命令结果 + **待裁决项**。
- 数字、文件行数、task id 一律以**当场跑出来的命令输出**为准，不要凭记忆。
