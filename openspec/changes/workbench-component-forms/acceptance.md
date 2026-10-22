# 验收清单 — workbench-component-forms

> 本文件是**本变更自带的验收基线**（沿用 `workbench-visual-language-v2` 与
> `graph-node-visual-language` 的体例）。
> 验收方式与它们同构：**自动断言 + 对照截图 + 键盘与焦点清单**三件套。
>
> 相关：`proposal.md`（范围与红线）、`design.md`（设计决策 D-1…D-8 · 待裁决 T-1…T-9）、
> `tasks.md`（任务拆解）、`specs/workbench-ui/spec.md`（**4 条 ADDED / 29 个 Scenario**）、
> `../workbench-visual-language-v2/decisions.md`（**A-115**）、
> `../workbench-visual-language-v2/design-notes/component-spec.md`（**§4.30** 形态权威）、
> `../workbench-visual-language-v2/acceptance.md`（**G-1…G-8** 底线守卫口径）。
>
> **标注约定**
> - **AUTO** —— 可由脚本 / 命令自动判定，产出机器可读的结果（PASS / FAIL）。
> - **SEMI** —— 半自动：脚本采集 + 人工判读（脚本负责把差异摆到眼前，判读由人做）。
> - **MANUAL** —— 必须人看 / 人按键。
>
> **被验收的形态（§4.30 权威）**
> §4.7 `select-spec`（触发器 + 浮起面板 + 选中项蓝洗底 + 行尾蓝点）·
> §4.16 `steps-num`（编号圆点 + 连接线）·
> §4.24 `dialog-spec`（暖墨面纱遮罩 + 浮起面板 + 右对齐动作区）·
> §4.25 `tool-line`（一行摘要）。

---

## 0. 底线守卫（最高优先级，先于其它任何检查）

> 冻结项：**请求与持久化不变**。冻结 = API 请求序列与载荷、持久化内容、学习事实、
> 状态机、由请求驱动的可见性切换。
> **本变更新增了四个界面，其中两个会抢焦点、一个会换掉 8 个表单控件的形态** ——
> ⇒ 这三条守卫的**风险面比前两条 change 更大**，不是更小。

| # | 检查项 | 判定方法 | 通过标准 | 类型 |
|---|---|---|---|---|
| **G-1** | **请求序列与载荷不得变** | 在**池副本**上脚本化跑一遍：① 一次完整练习（建卷 → 开始 → 逐题提交 → 自评 → 交卷 → 取答卷）；② 一次删除类流程（删试卷 / 删目标 / 删做题经验 / 删本地会话 / 整批回滚），**各跑两遍**（一遍确认、一遍取消）；③ 每次控件改动（切工作区 / 切章节 / 改排序 / 改答案展示时机 / 改目标类型 / 改模型 / 改发送方式 / 改运行中发送方式）。记录服务端收到的**请求方法 + 路径 + 载荷键集合**；改造前后各跑一次并 diff | 序列与载荷**逐条相同**；新增 / 删除 / 改名任意一条即 **FAIL**。⚠️ **自绘下拉的载荷仍由 hidden input 承载** —— 提交体里的**键集合与键值**必须与改造前逐字相同（`#goal-kind` 的 `kind` 键**只出现一次**） | **AUTO** |
| **G-2** | **持久化结果不变** | 同一次脚本化走查前后，比对池中 `problem_attempts` / `feedback_events` / `practice_runs` 的**行数与关键列** | 行数与关键列**逐行相同** | **AUTO** |
| **G-3** | **学习投影不变** | 同一份脚本化走查前后，比对受影响知识点 / 题目的当前状态与调度行 | **完全相同** | **AUTO** |
| **G-4** | **复习建议集合不变** | 比对改造前后同一时刻的到期项集合与弱项排序 | 集合与顺序**完全相同** | **AUTO** |
| **G-5** | **无新增学习事实** | 人工核对：本变更的改动只落在 `workbench.css` / `workbench.js` / `agent-ui.js` / `agent-ui.css` / `paper-practice.js` / `practice-flow.js` / `kp-experience.js` / `pages.py` | 池 schema **零变更**；`pool/` `pipeline/` `workbench/data/` **零改动**；**不新增统计行** | **AUTO** |
| **G-6** | **无新增持久字段** | `git diff --stat` + 池 schema 比对 | **零新增列、零新增行** | **AUTO** |
| **G-7** | **装饰层不拦截交互** | 检查所有新增装饰层（面板背景、骨架块、遮罩）的 `pointer-events` | 装饰层一律 `none`；可交互元素**不在**装饰层内；遮罩**可点但不关闭**（见 §3 K-13） | **AUTO** |
| **G-8** | **焦点顺序未因改造而改变** | 键盘 Tab 遍历录制**改造前 / 改造后**的**全页焦点停靠点序列**（含 id / 角色 / 文案） | 停靠点**数量相同、顺序相同**；**除**新出现的对话框（它打开时接管、关闭时归还）与**除**新增控件占用的那一个停靠点外，序列相同。⚠️ **自绘下拉与对话框都不得新增停靠点** | **AUTO** |

> 〔沿用 v2 口径〕G-1…G-4 的脚本要**同时**用于改造前与改造后，且跑在**池副本**上（见 §6）。
>
> 〔本变更特有〕**G-1 的两个高风险点**：
> ① **自绘下拉**：8 个控件里 `#goal-kind` 带 `name='kind'` ⇒ 若原生 `<select>` 与隐藏域**同时**留在 DOM 里，
> 提交体就会**多一个 `kind` 键** ⇒ G-1 破。判定：改造后 DOM 里**每个控件只有一个载荷载体**。
> ② **对话框**：打开 / 取消**不得**发出任何请求；只有「确认」才发那**一个**请求。

---

## 1. 自动断言清单（可脚本判定）

> 每条给出**断言什么**与**怎么判**。这组是本变更的**主门禁**：
> 四条里有三条（B 类的 4.7 / 4.24 / 4.25）的核心行为都是**可断言的键盘与焦点行为**，
> 截图只能证明「长什么样」，证明不了「按下去会怎样」。

| # | 断言 | 怎么判 | 通过标准 | 类型 |
|---|---|---|---|---|
| **A-1** | **8 处原生 `<select>` 已替换** | `grep -c "<select" workbench/server/pages.py` + 逐处核对 | 8 处**全部**由自绘控件承载；DOM 里残留的原生 `<select>` **只允许是「无脚本回落」那一份**（且在有 JS 时**不在 DOM 里**） | **AUTO** |
| **A-2** | **hidden input 承载载荷** | 逐个控件读 `document.getElementById(原 id)` 的 `tagName` 与 `value` | 8 个控件的值载体都是**隐藏域**；**`id` 与改造前相同**（⇒ 现有读取代码零改动）；`#goal-kind` 的 `name='kind'` **保留** | **AUTO** |
| **A-3** | **提交载荷键集合不变** | 提交一次表单，读提交体 | 键集合与键值与改造前**逐条相同**；`kind` **只出现一次** | **AUTO** |
| **A-4** | **自绘下拉的 ARIA** | 脚本读 8 个触发器与面板 | 触发器：`role=combobox` + `aria-expanded` + `aria-controls` + `aria-haspopup=listbox` +（打开时）`aria-activedescendant`；面板：`role=listbox` + `aria-labelledby`；项：`role=option` + `aria-selected` + id 唯一。**八项逐条成立** | **AUTO** |
| **A-5** | **自绘下拉的键盘模型** | 脚本逐键派发 | 关闭：`Enter`/`Space`/`↑`/`↓` 打开（活动项 = 当前已选项）；打开：`↑`/`↓` **循环**移动、`Home`/`End` 到首末、`Enter`/`Space` 提交、`Esc` **关闭且值不变**、可打印字符**首字母跳转**。**每条都有断言** | **AUTO** |
| **A-6** | **自绘下拉的焦点模型** | 脚本读 `document.activeElement` | 打开面板后 `activeElement` **仍是触发器**（**不是**选项）；`aria-activedescendant` 指向的元素存在且 `role=option`；关闭后 `activeElement` **仍是触发器** | **AUTO** |
| **A-7** | **自绘下拉只占一个 Tab 停靠点** | Tab 遍历 | 该控件在序列里**只出现一次**；打开面板**不新增**停靠点 | **AUTO** |
| **A-8** | **无脚本回落** | 禁用 JS 后走一遍 | 8 个控件**都还能选值**；提交载荷与改造前**逐条相同** | **AUTO** |
| **A-9** | **分段进度条的 ARIA 与非控件性** | 脚本读容器 | `role=progressbar` + `aria-valuenow` + `aria-valuemin` + `aria-valuemax` + `aria-label` 齐备；**无 `tabindex`**；Tab 序列里**没有**它；点击它**不产生任何请求** | **AUTO** |
| **A-10** | **分段进度条的溢出折叠** | 造一个 12 步的宿主 | 折叠为紧凑摘要，摘要里**带数字**（「完成 n / 共 m」）；**不是**把点挤成一条线 | **AUTO** |
| **A-11** | **分段进度条不新增统计** | 走查前后比对池 | `problems` / `problem_attempts` / `feedback_events` / `practice_runs` 的**行数与关键列逐行相同** | **AUTO** |
| **A-12** | **对话框的 ARIA 与焦点** | 脚本 | 面板：`role=dialog` + `aria-modal=true` + `aria-labelledby`（指向标题）；打开时 `activeElement` **在面板内**且**默认是「取消」**；背景内容 **`inert`**（背景里的按钮**点不到**）；`Esc` 关闭后 `activeElement` **是触发元素**；人为移除触发元素后关闭 ⇒ `activeElement` **不是 `body`** | **AUTO** |
| **A-13** | **对话框的焦点陷阱** | 打开后连按 `Tab` 20 次 + `Shift+Tab` 20 次 | `activeElement` **始终**在面板内的元素集合里；**到不了**背后页面 | **AUTO** |
| **A-14** | **对话框不提前发请求** | 打开 / 取消 / `Esc` / 点遮罩 | 四种路径**都不产生任何请求**；只有「确认」产生**一个**请求，且与改造前 `window.confirm` 之后的那一个**逐条相同** | **AUTO** |
| **A-15** | **原生确认框已清零** | `grep -rn "window.confirm" workbench/server/static/*.js` | 命中 **= 0** | **AUTO** |
| **A-16** | **工具调用卡的 ARIA** | 脚本读卡片 | 头行是 `<button>` 且带 `aria-expanded` + `aria-controls`；详情区 `role=region` 且有可访问名（`aria-labelledby`）；`aria-expanded` 随开合翻转 | **AUTO** |
| **A-17** | **工具调用卡的取值来源** | 造「无时长」「无证据」两个活动 | 「无时长」⇒ 卡片**没有**耗时那一格（**不显示占位**）；「无证据」⇒ 卡片写「未知」，**不**由动作名推断成功 | **AUTO** |
| **A-18** | **工具调用卡不重复行** | 跑一遍 Pi 活动更新 | 按活动 id **原地更新**，**不产生重复行** | **AUTO** |
| **A-19** | **命中区下限** | 逐个新控件量 `getBoundingClientRect()` + 伪元素补偿 | 每个新增可交互控件的**命中区 ≥ 44×44 CSS px**（视觉尺寸可小于 44） | **AUTO** |
| **A-20** | **焦点环没被压死** | `getComputedStyle` 读 focus-visible 下的 `outline-style` / `box-shadow` | **不得**是 `outline-style: none` 且无替代环；浮层内的环**不得**被 `overflow: hidden` 裁掉 | **AUTO** |
| **A-21** | **reduced-motion 降级** | `prefers-reduced-motion: reduce` 下截图 | 四个组件的终态帧与开启动效的终态帧**逐像素相同** | **AUTO** |
| **A-22** | **章节透镜的面板已并入统一控件** | `grep -c "chapter-lens-panel\|chapter-lens-option" workbench/server/static/*.js workbench/server/static/*.css` | 命中 **= 0**（**不留两套实现**）；章节切换仍是**同一个端点、同一个载荷键 `{chapter}`**（**不新增请求**） | **AUTO** |

---

## 2. 对照截图清单

> 每个条目产出**改造前 / 改造后**并排图（同一视口 **1440×900**、同一数据状态、同一滚动位置）。
> **改造前**基线：仓库现有的 `tmp/frontend-audit/00-baseline-*.png`（能复用的复用）；
> 改造后同路径同命名规则另出一套。
>
> 〔判据形态说明〕本变更**不是**整版重做 —— 它只动**四个组件**。
> ⇒ 判据以**组件级局部对比**为主（同一组件的前后并排），
> 页面其余部分**应当逐像素不变**（若变了 ⇒ 越界，FAIL）。

| # | 状态 | 必看的点 | 类型 |
|---|---|---|---|
| S-1 | 自绘下拉 · **关闭态**（8 处各一张） | 触发器形态与命中区；无原生下拉箭头 | **SEMI** |
| S-2 | 自绘下拉 · **打开态** | 浮起面板 + 抬升；选中项**蓝洗底 + 行尾蓝点**（**两处都要看见**） | **SEMI** |
| S-3 | 自绘下拉 · **错误态 / 禁用态 / 取值中** | 三态各一张；错误态红边 + 红洗底 | **SEMI** |
| S-4 | 自绘下拉 · **章节透镜**（顶栏） | 选项**只有章节名**；⚠️ **不得出现每章计数**（既有 `Chapter switch in the top bar` 明令） | **MANUAL** |
| S-5 | 自绘下拉 · **窄屏（768 / 1024）** | 面板贴触发器全宽、不横向溢出、不裁切 | **SEMI** |
| S-6 | 分段进度条 · **默认 / 完成 / 失败** | 编号圆点 + 连接线；四态**几何各不相同**（灰度下也要能分辨） | **SEMI** |
| S-7 | 分段进度条 · **溢出折叠** | 折叠成紧凑摘要且**带数字** | **SEMI** |
| S-8 | 对话框 · **默认** | 暖墨面纱遮罩 + 浮起面板 + **右对齐**动作区；面板**不是**半透明的；遮罩**没有**背景模糊 | **SEMI** |
| S-9 | 对话框 · **失败态** | 面板**不关**；顶部行内错误条；焦点仍在面板内 | **SEMI** |
| S-10 | 对话框 · **删除试卷确认** | 文案与按钮；**「取消」是默认焦点**（打开时焦点在取消上） | **MANUAL** |
| S-11 | 工具调用卡 · **折叠态** | **一行**头（状态点 + 工具名 + 耗时 + 箭头）+ 摘要一行 + 详情收起 | **SEMI** |
| S-12 | 工具调用卡 · **展开态 / 运行中 / 失败态** | 展开区是 `region`；运行中摘要位是**呼吸式**骨架（**不是**横扫）；失败态**全文无红字** | **SEMI** |
| S-13 | **夜纸**（同一批状态的夜纸版） | 四组件的夜纸取值；对比度达标 | **SEMI** |

---

## 3. 键盘与焦点清单（逐条可勾）

### 3.1 自绘下拉（§4.7）

- [ ] K-1 Tab 到触发器 ⇒ **有可见焦点环**（不得被 `outline: none` 压死）
- [ ] K-2 `Enter` / `Space` / `↓` / `↑` ⇒ 面板打开，**焦点仍在触发器**
- [ ] K-3 `↑` / `↓` ⇒ 活动项移动且**循环**；`Home` / `End` ⇒ 到首 / 末
- [ ] K-4 输入字母 ⇒ **首字母跳转**（连续输入有缓冲）
- [ ] K-5 `Enter` / `Space` ⇒ **提交**，面板关闭，焦点仍在触发器，触发器显示新值
- [ ] K-6 `Esc` ⇒ 关闭，**值不变**，焦点仍在触发器
- [ ] K-7 `Tab`（面板打开时）⇒ 关闭面板、**值不变**、焦点移到下一个控件〔**待裁决 T-1**〕
- [ ] K-8 面板打开时 **Tab 序列不被改变**（不新增停靠点）

### 3.2 工具调用卡（§4.25）

- [ ] K-9 Tab 到头行按钮 ⇒ 有焦点环；`Enter` / `Space` ⇒ 展开 / 收起；`aria-expanded` 同步翻转
- [ ] K-10 展开区是 `role="region"` 且**有可访问名**；屏幕阅读器能读到「已展开 / 已收起」

### 3.3 分段进度条（§4.16）

- [ ] K-11 Tab 序列**跳过**它（纯显示）；点击它**无反应、无请求**
- [ ] K-12 屏幕阅读器能读到「完成 n / 共 m」

### 3.4 对话框（§4.24）

- [ ] K-13 打开 ⇒ 焦点进面板、**默认落在「取消」**；背景内容 `inert`（点不到）
- [ ] K-14 `Tab` / `Shift+Tab` ⇒ **只在面板内循环**（**焦点陷阱**）
- [ ] K-15 `Esc` ⇒ 关闭；焦点**回到触发元素**
- [ ] K-16 触发元素已消失时 ⇒ 焦点落到**它所在的区域**，**不在 `body` 上**
- [ ] K-17 点击**遮罩** ⇒ 面板**不关**、焦点**留在面板内**〔**待裁决 T-5**〕
- [ ] K-18 失败 ⇒ 面板**不关**、错误就地报告、焦点**留在面板内**

### 3.5 全局

- [ ] K-19 页面转场与浮层（吐司 / 骨架屏）出现时**不抢焦点**（只有对话框接管）
- [ ] K-20 改造前后的**全页 Tab 停靠点序列**相同（数量 + 顺序）

---

## 4. 逐条 Scenario 判定（对应 `specs/workbench-ui/spec.md` 的 29 个 Scenario）

> 每一行给出**怎么验**与**通过标准**。判定列与 §1 / §2 / §3 的条目对应，
> 便于「一条 Scenario ⇒ 至少一个可执行断言」。

| # | Scenario | 怎么验 | 通过标准 | 判定来源 | 类型 |
|---|---|---|---|---|---|
| SC-1 | Open the options with the keyboard | 脚本逐键 | 面板打开 + 活动项 = 当前已选项 + 焦点在触发器 | A-5 / A-6 | **AUTO** |
| SC-2 | Move to an option and choose it | 脚本 | 活动项下移 + 提交 + 面板关闭 + 触发器显示新值 + 焦点在触发器 | A-5 | **AUTO** |
| SC-3 | Leave without choosing | 脚本 | 面板关闭 + 值**未变** + 焦点在触发器 | A-5 / A-6 | **AUTO** |
| SC-4 | Jump to an option by its first letter | 脚本 | 活动项跳到下一个以该字母开头的选项 | A-5 | **AUTO** |
| SC-5 | The tab order is not disturbed | Tab 遍历 | 一个停靠点 + 打开不新增 + 关闭回到触发器 | A-7 / G-8 | **AUTO** |
| SC-6 | The reported field is unchanged | 录请求 + 读提交体 | 方法 / 路径 / 载荷键集合**逐条相同** | G-1 / A-3 | **AUTO** |
| SC-7 | The options are announced | 读 ARIA 属性 | combobox + expanded + listbox + option/selected **齐备** | A-4 | **AUTO** |
| SC-8 | Without scripting the options are still offered | 禁 JS | 选项与值与改造前**逐条相同** | A-8 | **AUTO** |
| SC-9 | Count the steps | 截图 | 编号点 + 连接线 + 编号可读 | S-6 | **SEMI** |
| SC-10 | The state is not carried by colour alone | 灰度截图 | 四态**几何各不相同** | S-6 | **SEMI** |
| SC-11 | The indicator is not a control | Tab + 点击 | 被跳过 + 不发请求 | A-9 | **AUTO** |
| SC-12 | Too many steps collapse into a summary | 造 12 步宿主 | 折叠摘要**带数字** | A-10 / S-7 | **AUTO** |
| SC-13 | No new figure is invented | 池比对 | 行数与关键列**逐行相同** | A-11 / G-5 | **AUTO** |
| SC-14 | Without motion the final state is the same | reduced-motion 截图 | 与开启动效的终态帧**逐像素相同** | A-21 | **AUTO** |
| SC-15 | Open a modal dialog | 脚本 + 截图 | 面板 + 遮罩 + 背景不可用 + 焦点进面板 | A-12 / S-8 | **AUTO** |
| SC-16 | Escape closes the dialog | 脚本 | 关闭 + 焦点归还 | A-12 | **AUTO** |
| SC-17 | Focus stays inside the dialog | 连按 Tab | 焦点**始终**在面板内 | A-13 / K-14 | **AUTO** |
| SC-18 | The backdrop does not dismiss the dialog | 点击遮罩 | 面板仍在 + 焦点仍在面板内 | K-17 | **AUTO** |
| SC-19 | A failure is reported in place | 造失败 | 面板不关 + 就地报错 + 焦点在面板内 | K-18 / S-9 | **AUTO** |
| SC-20 | The existing confirmations use the dialog | 逐条走 6 类确认 | 弹的是**自家对话框**；确认前**无请求** | A-14 / A-15 | **AUTO** |
| SC-21 | The Agent approval stays inline | 触发 Agent 审批 | 审批**仍是对话流里的卡**、**不是**模态 | 人工 + `git diff` | **MANUAL** |
| SC-22 | Without motion the dialog is simply there | reduced-motion 截图 | 与开启动效的终态帧**逐像素相同** | A-21 | **AUTO** |
| SC-23 | One line carries the summary | 截图 | 单行头 + 摘要可读 + 详情收起 | S-11 | **SEMI** |
| SC-24 | Open the detail with the keyboard | 脚本 | 展开为 `region` + `aria-expanded` 翻转 + 再按收起 | A-16 / K-9 | **AUTO** |
| SC-25 | The time comes from evidence | 造无时长活动 | **没有**耗时那一格 | A-17 | **AUTO** |
| SC-26 | Unknown impact stays unknown | 造无证据活动 | 写「未知」+ 不推断成功 | A-17 | **AUTO** |
| SC-27 | Failure is carried by the marker | 造失败活动 | 状态点承担 + 摘要有界 + **全文无红字** | S-12 | **SEMI** |
| SC-28 | The card is announced | 读 ARIA | 头行有可访问名 + 报告开合状态 | A-16 | **AUTO** |
| SC-29 | Without motion the running card is simply there | reduced-motion 截图 | 与开启动效的终态帧**逐像素相同** | A-21 | **AUTO** |

---

## 5. 通过标准

本变更**通过**需同时满足：

1. §0 的 **G-1…G-8 全绿**（任何一条红即整体 **FAIL**，不进入后续评审）；
2. §1 的 **A-1…A-22 全部通过**（**AUTO** 项必须机器判**PASS**，不接受人工目测替代）；
3. §2 的 **S-1…S-13** 逐条判读通过，且**组件之外**的页面区域**逐像素不变**（越界变化 ⇒ **FAIL**）；
4. §3 的 **K-1…K-20 全部勾选**，或未勾选项**逐条列出**并说明为何可接受；
5. §4 的 **29 个 Scenario 全部有判定结论**（AUTO 项**必须**有脚本输出佐证）；
6. **既有需求逐字继续成立**：`Provider activity cards show evidenced outcomes` ·
   `Failed activities expose a concise error summary` · `Pi activities are conversation messages` ·
   `Chapter switch in the top bar` · `Focus visibility and contrast floors` ·
   `Complete primary learning text` —— 归档前**逐字复核**；
7. `openspec validate workbench-component-forms --strict` ·
   `openspec validate --specs --strict` · `python -m pytest tests -q` 三条**全绿**。

任一项不通过 → 回到 `design.md` 对应决策返工，
**不得**带着未过的底线项进入铺开阶段。

> ⚠️ **不许**为了让 S-* 变绿而**调大阈值**或**改基线**。

---

## 6. 走查执行协议（沿用仓库既有纪律）

> 术语「走查 / Scratch Walkthrough」见 `docs/GLOSSARY.md`：
> 「交付前的真实浏览器验证：在**池数据库副本 + 隔离注册表 + 独立端口**上种子数据
> 逐项点检（截图自检清单）。**永不写真实池。**」

- 在**池数据库副本 + 隔离注册表 + 独立端口**上执行，**永不写真实池**；
- §0 的 G-1…G-4 脚本、§1 的断言脚本、§2 的截图脚本、§4 的 Scenario 脚本
  **必须可重跑**，改造前后**各一份**，结果入库以便复现；
- 每个阶段的验收产出：对照截图组 + 断言报告 + 勾选后的键盘清单 + **未过项清单**；
- **前置固定**（沿用 `graph-isolation.md` §6.2 / §6.3）：
  视口 **1440×900** · `deviceScaleFactor = 1` · 浏览器缩放 100% ·
  截图前等 `document.fonts.ready` · 每次导航前清缓存 ·
  `window.scrollTo(0, 0)` 并断言；
- **先自证基线可复现**：正式比对前先连跑**两次改造前**基线并互比；
  若基线自身不可复现，**登记为待裁决项**，**不**默默放宽标准。
