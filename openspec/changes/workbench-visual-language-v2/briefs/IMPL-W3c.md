# IMPL-W3c — `practice-flow.js` + `paper-practice.js`：练习流程 · 挂载点迁移 · 音效落点 · 连对逻辑

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的
> **第 14 组（14.x 的 JS 侧）** · **第 17 组（17.1–17.4 / 17.8 的逻辑侧）** ·
> **10.5 / 10.6 的音效落点核对** · **6.2 / 6.3 中属于这两个文件的挂载点**。
> **只改 `workbench/server/static/practice-flow.js` 与 `workbench/server/static/paper-practice.js`。**

## 前置（自己核实，不要相信任何人的口头汇报）
1. `workbench.css` 已被别的 agent 改过（阅读层 `.wb-reading` + 动效 token + 分级降级闸门）——
   你只挂类名，**不要去改 CSS**。
2. 六个实现 agent 与你**同时在跑**，别人正在改 `workbench.js` / `pages.py` /
   `middle-navigation.js` / `records.py` / `workbench.css`。**你只碰这两个文件。**

## 硬约束
- **只改 `workbench/server/static/practice-flow.js` 与
  `workbench/server/static/paper-practice.js`**。不碰 `workbench.css` / `workbench.js` /
  `pages.py` / `middle-navigation.js` / `records.py` / `sfx.js` / `app.py` / `docs/` / `openspec/`。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **现有所有交互逻辑一个字都不许改**（所有者绝对底线）：
  请求序列、载荷键、DOM 身份、选项按钮的判定分支、自评、复习建议的请求与内容一律不动。
- **知识图谱**：这两个文件里若有图谱相关代码，一行都不许碰。
- **音效只在四个点发**（10.5）：答对 / 答错 / 完成 / 里程碑。
  **其它任何表面、事件或状态变化（hover、展开、导航、加载）一律不发声。**

## 必读
1. `tasks.md` 的 **第 10 组（10.3 / 10.5 / 10.6 / 10.7）** · **第 14 组** · **第 17 组** · **6.2 / 6.3**
2. `design-notes/motion-spec.md`（连对火苗、横幅、错误摆动的关键帧与参数化输入表）
3. `design-notes/component-spec.md`（选项控件 / 判定标记 / 连对计数器 / 横幅的组件形态）
4. `decisions.md` 的 **A-27 M-J / M-K**（火苗逐簇点亮与熄灭、错误摆动 ≤4px / 160ms 内结束 /
   **不做屏幕级震动**）· **A-27 M-H**（连对 >4 答错必须明示负反馈）· **A-29**（里程碑两个条件）·
   **A-38**（`sound` 字段名；庆祝爆点元素必须带 `lk-celebrate-burst` 或 `data-lk-cue="milestone"`）·
   **A-41**

## A. 6.2 / 6.3 的挂载点迁移
- `practice-flow.js` 里有 **9 处** `class='rich-text'`（题面 / 选项 / 解析 / 反馈 / 另一面 /
  提示面 / 作答 …），`paper-practice.js` 里有 **4 处**。
  全部改成 `class='wb-reading'`。
- **只改类名，不改内容、不改结构、不改顺序、不改 innerHTML 的其它部分。**
- ⚠️ **`.rich-text` 的 CSS 规则本轮不由你删**（CSS 侧另一个 agent 在动同一个文件，
  另有三个 agent 也在改别的文件里的挂载点）⇒ 本轮这两个文件里 `rich-text` 归零，
  全仓还不归零，**这是预期状态**（口径见 `decisions.md` **A-41**）。
- 题面处挂 `wb-reading wb-reading--stem`（若 grep 发现 CSS 侧还没有 `--stem` 这个类，
  就只挂 `wb-reading` 并在回报里说明）。

## B. 10.5 / 10.6 音效四落点（**核对 + 落位，不是新增功能**）
四个点必须**精确对应**：
1. **答对** → 练习流程里**判定正确**的分支（与 `.micro-verdict.ok` / `.option-correct` 同一处）；
2. **答错** → 同一分支的**判定错误**侧；
3. **完成** → 练习轮次结束、进入完成页的那一次响应；
4. **里程碑** → 庆祝**进入里程碑档**的那一拍（与几何爆点**同拍**，400ms）。

落点写法：调用既有的 `workbench/server/static/sfx.js`（**不要改 `sfx.js` 本身**）。
- 首次音效必须发生在**一次用户手势之后**（浏览器自动播放限制）；首屏加载**零发声**。
- **静音偏好**字段名是 **`sound`**（布尔，默认**开**），存在既有 `wb_settings_<工作区>` JSON 里；
  关闭时**立即生效、无需刷新**，且**不移除任何视觉反馈**（声音不是唯一通道）。
  `window.lkSfx.setEnabled()` 是既有入口 —— **复用它**。
- 里程碑音效与几何爆点**落在同一拍**，不早不晚。
- 验证：`grep -rn "playCue\|new Audio\|Audio(" workbench/` 的**调用点恰好 4 处**。

## C. 第 17 组 · 连对反馈的逻辑侧
- **17.1** 三级连对计数器：**灰 → 黄 → 黄→蓝渐变**（黄承载「当前做得顺」）。
  数字用 **Ticker 方式滚动**（vanilla rAF，只写 `textContent`；**不引第三方库**）。
  ⚠️ 通用 Ticker 的**实现**在 `workbench.js`（另一个 agent 负责）—— 你只**调用**它，
  **不要在两个文件里各写一份**。**先 grep `workbench.js` 确认那个 API 的名字**；
  若它还不存在，**不要自己造一个** —— 改为在回报里登记「等 `workbench.js` 的 Ticker API」，
  并用一种**不依赖该 API**的降级写法（直接写最终值）把功能做完整。
- **17.2** **一份**参数化横幅：5 连 / 10 连插播**同一份**横幅，数字用参数化输入切，
  不是每个数字一份。
- **17.3** 连对**> 4** 时答错**必须**给明确负反馈（`lk-error-nudge`），
  **不得沉默**，并把计数器复位。
- **17.8** 火苗簇**逐簇点亮**；断裂时**逐簇熄灭**并给负反馈，同时计数器复位。
  火苗是**连对进度的几何冗余通道**（计数器被滚出视口时长度仍可读）。
  ⚠️ 火苗是**内联 SVG**（灰 / 黄两层交叉淡入，**只动 opacity**）。
  ⇒ **火苗的 DOM 归谁？** 若 CSS 侧（`workbench.css`）已提供 `.lk-flame` 样式，
  你只**切 class**（`lk-flame.is-lit` 之类）；**不要自己写 SVG**，
  先 grep `workbench.css` 确认类名与所需结构。

## D. 14 组 · 标志带与中栏版式的 JS 侧
- 14 组主要是 CSS 与服务端侧；JS 侧只做**必要的 class 切换**（若任务书要求）。
  **不要**在 JS 里写一次性动效类名（见 21.5：切页会 innerHTML 替换，类名会被冲掉）。

## 验证
- 每完成一块就跑 AGENTS.md 四条验证命令：
  ```bash
  python -m pytest tests -q
  python -m compileall -q lessonkit.py workbench pipeline pool tests
  openspec validate --specs --strict
  python lessonkit.py guard extract-problems --course dmath --chapter ch06
  ```
- 四个音效场景各录一次（或用脚本断言调用点数量），确认**每个场景只触发一条、没有第五条**。
- 截图走查：答对 / 答错 / 完成 / 里程碑四个时刻 + 连对 1/3/5/10 连四个时点 + 一次断裂负反馈。
  **图谱页必须逐像素零变化**（G-5）。

## 落盘纪律与回报
- **小步提交**：每完成一块（迁移 / 音效落点 / 连对逻辑）**单独 commit**。
  **不要 `git add -A`** —— 只 add 你改的那两个文件。
- 若文件里出现**你没写过的改动**：先 `git diff` 看清楚再决定，**不要静默覆盖**。
- 最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **每个 commit 的内容** +
  **音效四个落点的文件与函数位置（贴代码）** + **连对计数器的状态存放位置** +
  **你调用 Ticker / 火苗 class 的实际写法** + **若 Ticker API 尚不存在，你用了什么降级写法** +
  四条验证命令结果 + **待裁决项**。
- 数字、文件行数、task id 一律以**当场跑出来的命令输出**为准。
