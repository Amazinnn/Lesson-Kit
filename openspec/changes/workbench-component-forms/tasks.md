# Tasks — workbench-component-forms

> **范围依据**：`proposal.md`（Why / What Changes / Capabilities / Impact）、
> `design.md` **D-1…D-8**（八节设计决策 + 待裁决项 T-1…T-9）。
> **形态依据**：`../workbench-visual-language-v2/design-notes/styleboard-picks.md`
> 与 `component-spec.md` **§4.30**（唯一形态定义）+ §4.7 / §4.16 / §4.24 / §4.25 + §6；
> 裁决链 `../workbench-visual-language-v2/decisions.md` **A-115**。
> **行为契约依据**：`specs/workbench-ui/spec.md`（4 条 ADDED / 29 个 Scenario）。
> **验收口径依据**：`acceptance.md`（§0 底线守卫 G-1…G-8、§1 自动断言 A-1…A-22、
> §2 对照截图 S-1…S-13、§3 键盘与焦点清单 K-1…K-20、§4 Scenario 逐条判定（SC-1…SC-29）、
> §5 通过标准、§6 走查协议）。
>
> **实施口径**
> - **先规格后代码**（AGENTS.md 纪律 1）：本 change 只落规格；**实现另起 PR**。
> - **不写池、不新增持久字段、不新增学习事实、不新增统计行**；
>   `pool/` `pipeline/` `workbench/data/` 一行不动。
> - **请求契约冻结**：方法 / 路径 / 载荷键集合**逐条不变**（**G-1**）。
> - **Tab 序列冻结**：既有 Tab 停靠点的**数量与顺序不变**（**G-8**）。
> - **命中区 ≥ 44×44 CSS px、焦点环不被压死**是**唯一不可让步**的尺寸约束
>   （A-115.2）；其余尺寸数字**可调**。
> - **无框架、无构建步骤、无 npm、无 CDN、无外部图标字体**；纯 CSS + 原生 JS + 内联 SVG。
> - **不碰** `openspec/changes/workbench-visual-language-v2/**` 与
>   `openspec/changes/graph-node-visual-language/**`（别人的地盘）。
>
> **九条待裁决项（T-1…T-9）** 在 `design.md` D-7：
> **T-1** Tab 是否提交活动项 · **T-2** 窄屏与打印回落的档位 ·
> **T-3** 编号点上限取几个 · **T-4** 分段进度条要不要可点 ·
> **T-5** 遮罩点击是否关闭 · **T-6** Agent 审批门要不要提为模态 ·
> **T-7** 分段进度条的第一个宿主 · **T-8** 没有耗时是否显示占位 ·
> **T-9** 章节透镜的「章」开关与新触发器怎么摆。
> ⇒ **每组末尾标了「待裁决」的条目，一律先等所有者拍板再动手**，不自行选边。

---

## 1. 自绘下拉的控件本体（§4.7 · D-1）

- [ ] 1.1 在 `workbench/server/static/workbench.css` 新增 `.lk-select` 族规则（触发器 / 面板 / 选项 / 状态），照 `component-spec.md` §4.7 的形态（触发器 + 浮起面板 + 选中项蓝洗底 + **行尾 8px 蓝实心点**），但**尺寸数字按布局微调**、**命中区 ≥ 44×44 CSS px**（视觉高度可小于 44，用内距或伪元素补）。验证：截图里选中项同时有蓝洗底**与**行尾蓝点；`elementFromPoint` 在触发器可视边缘外 2px 处命中。
- [ ] 1.2 落实**四态几何**（默认 / hover / focus-visible / disabled）与三个额外态（loading / error / 打开）：focus-visible 画焦点环（**不得** `outline: none`）、loading 用 `aria-busy="true"` 且箭头位换成指示器、error 用红边 + 红洗底。验证：四种状态各截一张；computed `outline-style` 在 focus-visible 下不是 `none`。
- [ ] 1.3 落实**选中项的双通道**：蓝洗底 **+ 行尾蓝实心点**（几何通道）⇒ 状态不得只靠颜色。验证：把页面转灰度后仍能分辨「哪一项被选中」。
- [ ] 1.4 落实**键盘模型**（D-1.3 表）：面板关闭时 `Enter`/`Space`/`↑`/`↓` 打开；面板打开时 `↑`/`↓` 循环移动、`Home`/`End` 到首末、`Enter`/`Space` 提交、`Esc` 关闭**且不改值**、可打印字符做**首字母跳转**。验证：键盘脚本逐键断言，**每一条都有断言**；`Esc` 后 hidden 域的 `value` 与打开前逐字相同。
- [ ] 1.5 落实**焦点模型**：打开面板时**焦点不离开触发器**（用 `aria-activedescendant` 指向活动项，**不**用 roving tabindex）；关闭后焦点**在触发器**上。验证：打开后 `document.activeElement` 仍是触发器；`aria-activedescendant` 指向的 id 存在且 `role="option"`。
- [ ] 1.6 落实 **Tab 的语义**（**待裁决 T-1**）：本文件取「面板打开时 `Tab` **关闭面板、不改值**、焦点移到下一个控件」。验证：`Tab` 之后面板关闭、hidden 域的值不变、焦点落在下一个控件上。
- [ ] 1.7 落实 **ARIA**（D-1.4）：触发器 `role="combobox"` + `aria-expanded` + `aria-controls` + `aria-haspopup="listbox"` + 打开时的 `aria-activedescendant`；面板 `role="listbox"` + `aria-labelledby`；选项 `role="option"` + `aria-selected` + 唯一 id；图标 `aria-hidden="true"` + `focusable="false"`。验证：脚本断言八处属性逐项存在且 `aria-expanded` 随开合翻转。
- [ ] 1.8 落实**失败态**（D-1.7）：取值失败 ⇒ `error` 态 + `aria-invalid="true"` + **值不变**；选项为空 ⇒ 面板给一条明确文案而不是空白；脚本异常 ⇒ **降级回原生 `<select>`**（把原生 select 放回 DOM、移除隐藏域）。验证：人为抛异常后页面仍能选值，且提交载荷键集合不变。
- [ ] 1.9 阶段验收：跑 AGENTS.md 的四条验证命令（`python -m pytest tests -q` /
  `python -m compileall -q lessonkit.py workbench pipeline pool tests` /
  `openspec validate --specs --strict` /
  `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；
  并按 `acceptance.md` §1 **A-1…A-5** 与 §3 **K-1…K-8** 逐条走查。

## 2. 自绘下拉的 8 处接入与载荷红线（§4.7 · D-1.5）

- [ ] 2.1 在 `workbench/server/static/workbench.js` 写**一处**自绘下拉的初始化与事件绑定（**单一来源**，8 处复用，**不各写一份**）。验证：`grep -n "lk-select" workbench/server/static/workbench.js` 的**定义点**只有 1 处。
- [ ] 2.2 逐处替换（8 处，**无例外**）：`workbench/server/pages.py` 的
  `#chapter-lens-select`（:211）· `#paper-reveal-timing`（:376）· `#goal-kind`（:456）·
  `#knowledge-sort`（:650）· `#workspace-select`（:985）· `#setting-running-send`（:993）·
  `#ai-model-switch`（:1074）· `#ai-send-action`（:1100）。
  验证：`grep -c "<select" workbench/server/pages.py` 的命中只剩**无脚本回落**用的那一处（见 2.6）。
- [ ] 2.3 **hidden input 沿用原来的 `id` 与 `name`**（D-1.1），触发器与面板用 `{原 id}-trigger` / `{原 id}-panel` / `{原 id}-opt-{n}`。
  ⇒ **7 个由页面脚本读 `.value` 的控件现有读取代码一行不改**
  （`workbench.js:202 / 1301 / 1318 / 3259 / 4458 / 5183`、`paper-practice.js:32`）；
  `#goal-kind` 的 `name='kind'` **保留**。验证：`git diff` 显示这 7 处读取代码**零改动**。
- [ ] 2.4 **原生 `<select>` 在 JS 模式下从 DOM 移除**（不是 `display:none`）——否则 `#goal-kind` 会**多提交一个 `kind` 键** ⇒ **G-1 破**。验证：页面里 `document.querySelectorAll("select").length` 与「该控件的 hidden 域数量」之和不重复计；提交体里 `kind` **只出现一次**。
- [ ] 2.5 **选项集合与选项值逐条不变**；**不得**新增任何图（尤其 `#chapter-lens-select` **不得显示每章计数** —— 既有 `Chapter switch in the top bar` 明令）。验证：改造前后逐处比对选项的 **值集合**与**文案集合**，**逐条相同**；章节透镜的选项里没有任何数字。
- [ ] 2.6 落实**无脚本回落**（D-1.6）：服务端渲染的原生 `<select>` 原样保留（无脚本时它就是界面）；
  **窄屏**面板贴触发器全宽铺开、不裁切；**打印**只出当前值文本。
  〔**待裁决 T-2**：回落到底要哪几档〕验证：禁用 JS 后页面仍能选值并提交同样的载荷；窄屏下面板不横向溢出。
- [ ] 2.7 落实**页面既有 Tab 序列不变**（**G-8**）：改造前后各录一次全页 Tab 停靠点序列。验证：停靠点**数量相同、顺序相同**，控件只占**一个**停靠点。
- [ ] 2.8 **把已有的章节透镜自绘面板并进统一的 `.lk-select`**（D-1.8）：
  现状 `workbench.js:74-190` + `pages.py:207-213` + `workbench.css:613-660` 已有第二套实现
  （`.chapter-lens-panel` / `.chapter-lens-option`），它**焦点进面板**（`workbench.js:110`）、
  **关闭回开关**（`:117`）、**原生 select 留 DOM**（`:124`）—— 与 D-1 的口径三处不一致。
  ⇒ 这套面板必须**整体并入**共享控件，**不留两套实现**。
  〔**待裁决 T-9**：章节透镜的「章」开关与新触发器怎么摆〕
  验证：`grep -c "chapter-lens-panel\|chapter-lens-option" workbench/server/static/*.js workbench/server/static/*.css` 的命中 **= 0**；
  章节切换请求仍是**同一个端点、同一个载荷键 `{chapter}`**（**不新增请求**）——
  判定见 `acceptance.md` §1 **A-22**。
- [ ] 2.9 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §0 **G-1**（请求序列与载荷**逐条相同**）·
  §0 **G-8**（Tab 序列相同）· §1 **A-6…A-8** 逐条走查；并把改造前后的请求序列脚本**各留一份**入库。

## 3. 分段进度条（§4.16 · D-2）

- [ ] 3.1 在 `workbench/server/static/workbench.css` 新增 `.lk-steps` 族规则：**编号圆点 + 连接线**（圆点里放步骤序号），照 §4.16 的形态，**尺寸数字可调**。验证：截图里能看到「1 2 3 …」的编号与连接线。
- [ ] 3.2 落实**四态几何各不相同**（已完成 = 实心 / 当前 = 半填 / 未开始 = 空心环 / 失败 = 实心 + 叉）⇒ **不靠颜色也分辨得出**。验证：灰度截图里四态仍可分辨。
- [ ] 3.3 落实 **ARIA**：`role="progressbar"` + `aria-valuenow`（已完成步数）+ `aria-valuemin="0"` + `aria-valuemax`（总步数）+ `aria-label`。验证：脚本断言五个属性齐备且数值与可见步数一致。
- [ ] 3.4 落实**「不是控件」**：不进 Tab 序列（**无 `tabindex`**）、不可激活、**不发任何请求**。
  〔**待裁决 T-4**：若要可点，必须先另加一条可观察行为，不得在本组悄悄加〕验证：Tab 序列里没有它；点击它不产生任何请求。
- [ ] 3.5 落实**上限与溢出形态**（D-2.2）：编号点上限为**可调参数**（默认 **7**），
  〔**待裁决 T-3**〕超过上限**折叠为紧凑摘要**「已完成 n / 共 m」+ 一条胶囊进度带（**不是**把点挤成一条线）。
  验证：造一个 12 步的宿主 ⇒ 折叠摘要出现且**带数字**（数字就是几何通道）。
- [ ] 3.6 落实**取值来源**（D-2.4）：完成步数与总步数**只取宿主已有的值**；**不新增统计 / 比率 / 分数**；**不写池**。
  验证：池的 `problems` / `problem_attempts` / `feedback_events` / `practice_runs` 行数**零变化**。
- [ ] 3.7 落实**reduced-motion 降级**：直接呈现终态（不做逐个点亮）；终态与开启动效时**逐字相同**。
  验证：`prefers-reduced-motion: reduce` 下截图与开启动效的终态帧**逐像素相同**。
- [ ] 3.8 落实**宿主接入**（**待裁决 T-7**：第一个宿主是否为连对计数器的进度指示器）。
  若接入连对进度：v2 `Consecutive-correct escalation feedback` 的「逐簇点亮的指示器」**改由本组件承载**，
  连对的**语义、档位与横幅契约不变**。验证：连对到 5 / 10 时横幅仍按 v2 的契约插播。
- [ ] 3.9 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §1 **A-9…A-11** 与
  §3 **K-11…K-12** 逐条走查（形态、折叠、非控件性）。

## 4. 对话框的控件本体（§4.24 · D-3）

- [ ] 4.1 在 `workbench/server/static/workbench.css` 新增 `.lk-dialog-backdrop` / `.lk-dialog` 族规则：
  **暖墨面纱遮罩**（半透明落在**背景色自身**上，**不用**容器的 `opacity`；**不用** `backdrop-filter` 模糊）+
  浮起面板 + **右对齐**动作区。尺寸数字可调。验证：截图里面板**不是**半透明的；遮罩**没有**背景模糊。
- [ ] 4.2 落实 **ARIA**：`role="dialog"` + `aria-modal="true"` + `aria-labelledby`（指向标题）；打开时**面板之外**的内容加 `inert`。验证：脚本断言三个属性齐备；`inert` 生效后背景里的按钮**点不到**。
- [ ] 4.3 落实**焦点进入**（D-3.3）：打开时焦点移到面板内**第一个可聚焦元素**，**默认是「取消」**；面板内无可聚焦元素时焦点落在面板容器上（容器 `tabindex="-1"`）。验证：脚本断言打开后 `document.activeElement` 是「取消」按钮。
- [ ] 4.4 落实**焦点陷阱**：面板打开时 `Tab` / `Shift+Tab` **只在面板内循环**（最后一项 `Tab` 回第一项；第一项 `Shift+Tab` 回最后一项），**到不了**背后。验证：脚本连按 `Tab` 20 次，焦点**始终**在面板内的元素集合里。
- [ ] 4.5 落实**焦点归还**（D-3.3）：关闭后焦点**回到打开它的那个元素**；该元素已从 DOM 消失时，落到它**所在的区域**（最近的仍在的祖先容器），**不得**留在 `body` 上。验证：脚本断言关闭后 `document.activeElement` 是触发元素；人为移除触发元素后断言**不是** `body`。
- [ ] 4.6 落实 **`Esc` 关闭**与**遮罩点击不关闭**（**待裁决 T-5**：本文件取不关闭）。
  验证：`Esc` ⇒ 面板关闭 + 焦点归还；点击遮罩 ⇒ **面板仍在** + **焦点仍在面板内**。
- [ ] 4.7 落实**busy / error 态**：动作进行中面板**不关** + `aria-busy="true"` + 确认按钮切 loading 并禁用；
  失败时面板**不关** + 顶部行内错误条（红点 + 文字，`role="alert"`）+ **焦点留在面板内** + **值不变**。
  验证：脚本断言失败后 `document.activeElement` 仍在面板内，且 hidden 域的值未变。
- [ ] 4.8 落实 **reduced-motion 降级**：直接呈现终态（遮罩 + 面板已在位），终态与开启动效时**逐字相同**。
  验证：`prefers-reduced-motion: reduce` 下截图与开启动效的终态帧**逐像素相同**。
- [ ] 4.9 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §1 **A-12** 与 §3 **K-13…K-14**
  （焦点陷阱 + 焦点归还）逐条走查。

## 5. 六处原生确认改用对话框（§4.24 · D-3.5 / D-3.6）

- [ ] 5.1 在 `workbench/server/static/workbench.js` 写**一处**对话框的 API（打开 / 关闭 / 焦点归还 / busy / error），
  **单一来源**；6 处确认**复用**它，**不各写一份**。验证：`grep -n "lk-dialog\|dialogOpen" workbench/server/static/workbench.js` 的**定义点**只有 1 处。
- [ ] 5.2 逐处替换（6 处）：`kp-experience.js:149`（删除做题经验）· `workbench.js:3162`（删除试卷）·
  `workbench.js:3201`（放弃未完成练习 / 重新开始）· `practice-flow.js:1333`（当前知识点还有一轮未完成练习）·
  `workbench.js:3282`（删除目标）· `workbench.js:5026`（整批回滚）· `workbench.js:5543`（删除本地 Agent 会话）。
  ⇒ **合计 7 个调用点、6 类确认语义**（`workbench.js:3201` 与 `practice-flow.js:1333` 是同一类语义的两处调用）。
  验证：`grep -rn "window.confirm" workbench/server/static/*.js` 的命中 **= 0**。
- [ ] 5.3 落实**时序红线**（D-3.6）：**打开对话框不发请求** · **取消 / Esc / 遮罩点击不发请求** ·
  **确认才发那一个请求**，且**方法 / 路径 / 载荷键集合与改造前的 `window.confirm` 之后完全相同**。
  验证：改造前后各录一次「打开 → 取消」与「打开 → 确认」两条路径的请求序列，**逐条相同**（G-1）。
- [ ] 5.4 落实**Agent 内联确认卡保持内联**（D-3.5）：`agent-ui.js:351 confirm()` 的 `.agent-approval-card`
  **不改**（不动 DOM 结构、不提为模态）。验证：`git diff workbench/server/static/agent-ui.js` 中
  `confirm()` 与 `agent-approval-card` 相关代码**零改动**（除了第 6 组工具调用卡那一处）。
- [ ] 5.5 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §0 **G-1** ·
  §1 **A-14 / A-15** · §2 **S-10** · §4 **SC-20** 逐条走查。

## 6. 工具调用卡（§4.25 · D-4）

- [ ] 6.1 在 `workbench/server/static/workbench.css` 新增 `.lk-tool` 族规则：**头一行**（状态点 + 工具名 +
  耗时 + 展开箭头）+ **摘要一行** + **默认收起的详情区**（`--surface-base` 底 + 圆角 + 等宽字 + 横向可滚）。
  头行命中区 ≥ 44×44 CSS px。验证：截图里头行是一行；展开区默认收起。
- [ ] 6.2 落实**展开 / 收起的键盘路径**（D-4.2）：头行是**真 `<button>`**，带 `aria-expanded` + `aria-controls`；
  详情区 `role="region"` + `aria-labelledby`（指向头行按钮）；`Enter` / `Space` 展开与收起。
  ⇒ **这是本条的真实新增行为**：现状是原生 `<details>/<summary>`（`workbench.js:4648` / `:4716`），
  **没有 `aria-expanded`**。验证：脚本断言 `aria-expanded` 存在且随开合翻转；展开区有 `role="region"` 且有可访问名。
- [ ] 6.3 落实**取值来源**（D-4.3）：工具名 / 状态 / 结果 / 影响**只取活动自报的证据**；
  **耗时只取活动自报的时长**，**没有就不显示**（**待裁决 T-8**：是否显示占位 —— 本文件取整格不显示）；
  **影响未知就如实标为未知**，**不得**由动作名推断成功；失败摘要 **≤240 字**、**不展开即可读**。
  验证：造一个「无时长」的活动 ⇒ 卡片**没有**耗时那一格；造一个「无证据」的活动 ⇒ 卡片写「未知」；两者都不产生新数字。
- [ ] 6.4 落实**状态与几何**（D-4.4）：running = 蓝半填点 + 摘要位两行**呼吸式**骨架屏（**不是**横扫）；
  done = 实心点；failed = 红实心点 + 摘要末尾省略号（**不加红字**）；blocked = 红叉。
  验证：灰度截图里 running / done / failed / blocked **几何各不相同**；失败态**全文无红字**。
- [ ] 6.5 把 `.ai-plan-step`（`workbench.css:1791`、`workbench.js:4638`）与 `.ai-activity`
  （`workbench.css:1850`、`workbench.js:4705`）两套形态**合并为工具调用卡**，
  并把 `.ai-plan-output`（`workbench.css:1833`）并入详情区。**不保留两套实现。**
  验证：`grep -c "ai-plan-step\|ai-activity" workbench/server/static/*.css workbench/server/static/*.js` 的命中 = 0（或仅剩注释）。
- [ ] 6.6 保住**既有契约**（D-4.5）：按活动 id **原地更新、不产生重复行**；语义动作名 / 真实状态 /
  有证据的结果 / 未知即未知 / 诊断净化后默认折叠 / 摘要 ≤240 字 / **不提供后端不支持的选择性重试**。
  验证：跑一遍「Pi 命令完成」与「工具报错」两条既有场景，逐字对照 `openspec/specs/workbench-ui/spec.md:853 / 922 / 1384`。
- [ ] 6.7 落实 **reduced-motion 降级**：running 态直接是最终样子（骨架屏**不呼吸**）；展开 / 收起**直切**。
  验证：`prefers-reduced-motion: reduce` 下截图与开启动效的终态帧**逐像素相同**。
- [ ] 6.8 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §1 **A-16…A-18** ·
  §3 **K-9…K-10**（工具卡键盘路径）· §4 **SC-23…SC-29** 逐条走查。

## 7. 契约协调与交付（AGENTS.md 纪律 2 / 3）

- [ ] 7.1 **落 GLOSSARY 词条**：`design.md` D-6 的 **7 条**（自绘下拉 / 载荷承载域 / 焦点陷阱 /
  焦点归还 / 编号点串 / 工具调用卡（单行形态）/ 模态对话框）**必须**先在 `docs/GLOSSARY.md` 建条目
  （词条 / 定义 / 出处），再进正式文档。验证：GLOSSARY 里能查到这 7 条；
  `docs/PENDING-DEFINITIONS.md` 里**没有**本 change 遗留的未定义名词。
- [ ] 7.2 同步 `docs/PRODUCT-MANUAL.md`：新增 / 改写的章节（自绘下拉的操作与键盘 · 分段进度条的读法 ·
  对话框的打断与焦点 · 工具调用卡的一行读法）。验证：手册能逐条对上本 change 的用户可观察行为。
- [ ] 7.3 同步 `docs/ACTION-GRAPH.md`：**新增**「确认删除类动作」等被本 change 改变的入口
  （从原生 confirm 变成对话框 ⇒ **动作本身不变、交互形态变** ⇒ 登记为**改级**而非新增 / 退役）；
  复核是否有动作需要新增 / 退役。验证：ACTION-GRAPH 有对应记录。
- [ ] 7.4 **归档顺序协调**：v2 `workbench-visual-language-v2` **先归档**，本 change **后归档**；
  归档本 change 前**逐字复核** `Consecutive-correct escalation feedback`（v2）与
  `Provider activity cards show evidenced outcomes`（若被 v2 改写）的最终文本与本 delta 一致。
  验证：合并顺序在提交历史里可查；复核记录留痕。
- [ ] 7.5 复核**既有需求逐字继续成立**（D-8 第 4 条）：
  `Provider activity cards show evidenced outcomes` · `Failed activities expose a concise error summary` ·
  `Pi activities are conversation messages` · `Chapter switch in the top bar` ·
  `Focus visibility and contrast floors` · `Complete primary learning text`。
  验证：`git diff openspec/specs/workbench-ui/spec.md` 在归档前**零改动**（本 change 只动 `openspec/changes/`）。
- [ ] 7.6 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §5 的通过标准**逐条判定**；
  把**未过项**逐条列出（不许默默放宽标准）。

## 8. 边界护栏（D-8 逐项复核：明确不动的东西）

- [ ] 8.1 复核 **不新增请求、不改请求契约**：改造前后各录一次全流程请求序列（建卷 → 开始 → 逐题提交 →
  自评 → 交卷 → 取答卷 + 删试卷 / 删目标 / 回滚 + 切工作区 / 切章节 / 改排序 / 改模型 / 改发送方式）。
  验证：**方法 / 路径 / 载荷键集合逐条相同**（G-1）。
- [ ] 8.2 复核 **不写池**：`pool/` · `pipeline/` · `workbench/data/` **零改动**；
  `problems` / `problem_attempts` / `feedback_events` / `practice_runs` 的**行数与关键列逐行相同**；
  **零新增持久字段、零新增学习事实、零新增统计行**。验证：`git diff --stat` 这三处**零改动**。
- [ ] 8.3 复核 **Tab 序列不变**（G-8）：改造前后各录一次全页 Tab 停靠点序列。
  验证：停靠点**数量相同、顺序相同**；自绘下拉与对话框**各只占一个**停靠点，**不新增**。
- [ ] 8.4 复核 **Agent 契约不动**：`ai-teacher-bridge` 的活动事件、审批门、Artifact 语义一字不改；
  Agent 内联确认卡仍是内联卡。验证：`git diff` 里没有 `ai-teacher-bridge` 契约文件；
  `agent-ui.js` 的 `confirm()` **零改动**。
- [ ] 8.5 复核 **图谱不动**：知识图谱页不在本 change 范围内。
  验证：`git diff --stat` 里 `workbench.css` 的图谱区段**零改动**。
- [ ] 8.6 复核 **另两个 change 的目录不动**：`git status --short` 里
  `openspec/changes/workbench-visual-language-v2/**` 与
  `openspec/changes/graph-node-visual-language/**` **零条目**。
- [ ] 8.7 阶段验收：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §0 **G-1…G-8** 与 §5 逐条判定。
