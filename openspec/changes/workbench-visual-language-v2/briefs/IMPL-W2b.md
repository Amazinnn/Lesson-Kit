# IMPL-W2b — 工作台设置视图与偏好存储（HTML + JS + 静态缓存）

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 11 组（11.1–11.7）** · **5.4**。
> 改 `workbench/server/pages.py` · `workbench/server/static/workbench.js` · `workbench/server/app.py`。

## 必读
1. `tasks.md` 的 **第 11 组 / 5.4**（你的任务书，逐条实现）
2. `design.md` 的 **D-9**（设置视图形态与主题应用时机）与 **D-8**
3. `decisions.md` 的 **A-11**（主题默认：默认跟随系统、显式选择优先）·
   **A-2**（动效偏好同模式）· **A-7**（图谱出界，本变更不碰图谱）
4. `specs/workbench-settings/spec.md`（**新能力的 7 条 Requirement / 25 场景 —— 你的行为契约**）
5. `specs/workbench-ui/spec.md` 的 `Learner settings in the left rail`（MODIFIED 后的版本）
6. `design-notes/component-spec.md`（设置视图与四个偏好控件的规格）

## 硬约束
- **只改** `workbench/server/pages.py` · `workbench/server/static/workbench.js` ·
  `workbench/server/app.py`。
- **不要**改 `workbench/server/static/workbench.css`（**有并行 agent 正在改**）·
  不改 `records.py` / `practice-flow.js` / `paper-practice.js` / `docs/` / `openspec/`。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- 冻结：**请求与持久化不变**。偏好只进浏览器 localStorage，**零请求、零池写入**。
- **知识图谱完全不动**（A-8）。
- 无框架 / 无构建 / 无 npm / 无 CDN。

## 11.1–11.7 要点
- **11.1** `pages.py` 新增 `settings_page()`（**中栏**视图）；在 `app.py` 的 `_send_page`
  （约 L234-261）注册 `/w/{name}/settings` 分支。
  该视图**只承载外观偏好**（主题 / 阅读字面 / 动效 / 声音），
  **不得**托管任何改变学习行为的控件（既有 spec 把自评开关钉在左栏）。
  每个偏好是一个**自带名称与当前值**的控件，**不加解释性散文**（少字原则）。
- **11.2** 左栏设置区新增一个控制，开 / 关设置视图；关闭后中栏**回到打开前的视图**。
  ⚠️ **既有两项行为偏好（运行中发送方式、练习显示自评，`pages.py:659-668`）留在左栏原位**，
  **不得搬走**（用户可感知的位置不能无声搬动）。
- **11.3** 偏好存储**复用既有键** `wb_settings_<工作区>`（`workbench.js:165` 的 `SETTINGS_KEY`），
  四个外观偏好作为**同一 JSON 对象的四个新键**，与既有 `showRating`（`:188`）、
  `runningSendAction`（`:503`）并列。**不新增 localStorage 键、不落服务端、不写池。**
  删掉存储后主题回到**跟随系统**（A-11）。
- **11.4** **首屏无 FOUC**：主题属性挂 `<html>`（`dataset.theme = "night" | ""`），
  在 `pages.py` 的 `_base`（约 L1096）`<head>` 内、样式表 `<link>` **之前**放一段内联脚本，
  同步读偏好并写 `dataset.theme`。读取顺序按 **A-11**：
  **无已存偏好** ⇒ 读系统 `prefers-color-scheme`（`matchMedia`）；
  **有已存偏好** ⇒ 读它；两者都写 `<html data-theme>` ⇒ 首屏无闪烁；
  **无 JS 时降级为亮色**（暖奶油）。显式选择**优先并覆盖**系统。
- **11.5** 设置视图走 `middle-navigation.js` 的**同工作区导航路径**，
  `#ai-column` DOM 与 Agent 控制器**保持挂载**（既有 spec「Same-workspace middle navigation
  preserves the Agent rail」）；开关前后是**同一实例**，不丢滚动位置与草稿输入。
- **11.6** 动效偏好的**分级降级**在 JS 侧：三处编排各自 `matchMedia`
  （参照 `workbench.js:1639`）。四种组合的判定见 `tasks.md` 11.6。
  ⚠️ **CSS 侧的分级降级由另一个 agent 负责**（`workbench.css:733` 与 `:1126-1131` 的
  全局闸门）—— 你只做 JS 侧的 `matchMedia` 判定与偏好读写，**不要**改 CSS。
  两者靠同一套判定口径对齐（判定线写进 `design.md` D-7）。
- **5.4** 字体资源缓存策略：`app.py` 的 `_send_static`；`CONTENT_TYPES`（L26-34）已含
  `.woff2` / `.woff`（若你为音效补了 `.mp3` / `.ogg`，一并加上）。
  改 CSS 或字体必须**立刻**到达用户。

## 验证
- 每组末尾跑 AGENTS.md 四条验证命令。
- 截图走查：设置视图**亮 / 暗**两主题；夜纸首帧截图即为夜纸（无浅色闪帧）；
  系统暗色 + 无已存偏好时首帧即为夜纸；显式选暖纸后系统为暗色也仍是暖纸首帧。
- 确认整条设置链路**零请求、零池写入**，且切换偏好**不改变任何视图内容、列表顺序、计数与调度**。
- 浏览器前进 / 后退同样保持同一 Agent 实例。

## 落盘纪律与回报
2 分钟内先落 `settings_page()` 骨架 + 路由分支，再逐步推进。
最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **FOUC 四种组合的实测**（首帧底色）+
**偏好键名与落点**（复用 `wb_settings_<工作区>` 的证据）· **零请求/零池写入的验证方式** +
**Agent 栏同一实例的验证** + 四条验证命令结果 + 待裁决项。