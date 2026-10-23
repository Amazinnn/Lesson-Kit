# Proposal — workbench-component-forms

> **形态依据（已拍板，本提案不重新裁决）**：
> `openspec/changes/workbench-visual-language-v2/design-notes/styleboard-picks.md`
> 的所有者裁定（2026-10-22，存储键 `lk-styleboard-v2`），
> 落点为 `design-notes/component-spec.md` **§4.30 组件形态裁定表**（§4.30 是**唯一形态定义**，
> 冲突时 §4.30 > 各节裁定框 > 各节正文），裁决链为
> `decisions.md` **A-115**。
>
> **本 change 的四条全部落在 A-115 的 B 类**（§4.30.1）：
> 4.7 自绘下拉 · 4.16 分段进度条 · 4.24 对话框 · 4.25 工具调用卡。
> A 类的 24 条是**现有产品的形态变更**（只改外观），由另外两波实现，**不在本 change 范围内**。
>
> **本 change 只写规格，不写产品代码**（AGENTS.md 纪律 1：需求先落文档再动代码）。

---

## Why

所有者做了一次**组件样式一览**（样式板），为每个组件挑出了唯一形态。
其中 **24 条是现有产品的形态变更**——只换一层皮，不改行为、不改请求 ⇒ 可以直接实现。
**剩下 4 条在产品里根本没有对应界面**：它们要**引入新的用户可观察行为**，
而不是改外观。实现它们之前必须先把行为写进规格，否则实现者只能凭猜测定键盘模型、
ARIA 角色与焦点去向，而这三样恰好是最容易做错、也最难在事后发现的部分。

| § | 组件 | 产品现状 | 缺的是什么 |
|---|---|---|---|
| 4.7 | 自绘下拉 | **8 处原生 `<select>`**（`workbench/server/pages.py`） | 键盘模型 · ARIA 角色 · 焦点去向 · 载荷如何仍由 hidden input 承载 |
| 4.16 | 分段进度条 | **没有这个界面** | 段数上限 · 溢出形态 · 是否可点（可点就要新行为） |
| 4.24 | 对话框 | 只有**原生 `window.confirm()`** 与 **Agent 内联确认卡** | Esc 关闭 · 焦点陷阱 · **焦点归还** · 遮罩点击是否关闭 · `role=dialog` + `aria-modal` |
| 4.25 | 工具调用卡 | 最接近的是 `.ai-activity` / `.ai-plan-step` / `.ai-plan-output` | 「工具名 + 耗时」的取值来源 · 折叠与展开的键盘路径 · 失败态的语义 |

这四条里藏着两条**不可让步的红线**：

- **G-1（请求序列与载荷不得变）** —— 自绘下拉把原生控件换掉，最容易顺手改掉提交载荷。
  ⇒ 规格必须写死「**载荷仍由 hidden input 承载**」「请求的方法 / 路径 / 载荷键集合逐条不变」。
- **G-8（焦点顺序不得被打乱）** —— 自绘下拉与对话框都会抢焦点，最容易打乱既有 Tab 序列。
  ⇒ 规格必须写清「**打开时焦点去哪**」「**关闭后焦点还给谁**」。

还有一条**必须写进规格、不能当成可选项**的：无障碍缺陷（藏起来的键盘陷阱、
焦点回不到原处）不是「可以以后再修」的选项，**是必须实现的行为**。

⇒ 因此单开一个 change（`workbench-component-forms`）承载这四条，
**先 proposal → specs，再谈实现**；A 类不阻塞。

---

## 背景与证据

### 现状实测（本 change 起草时复算）

| 事实 | 证据 |
|---|---|
| 原生 `<select>` **8 处** | `workbench/server/pages.py:211 / 376 / 456 / 650 / 985 / 993 / 1074 / 1100` |
| 其中**只有 1 处**带 `name`（进表单载荷） | `#goal-kind name='kind'`；其余 7 处由页面脚本读 `.value` |
| 原生确认框 **6 处** | `kp-experience.js:149` · `practice-flow.js:1333` · `workbench.js:3162 / 3201 / 3282 / 5026 / 5543` |
| Agent 内联确认卡 | `agent-ui.js:351 confirm()` → `.agent-approval-card`（**受 Agent 契约管**） |
| 工具调用相关类 | `workbench.css:1791 .ai-plan-step` · `:1850 .ai-activity` · `:1833 .ai-plan-output` |
| 展开目前是原生 `<details>/<summary>` | `workbench.js:4648` / `:4716` ⇒ **没有 `aria-expanded`** |
| 已有一段自绘面板先例 | `pages.py:207` `#chapter-lens-select` + `:210` `.chapter-lens-panel role=listbox`；`workbench.css:615` 在有 JS 时把原生 select 藏掉 |
| ⚠️ **那段面板是「同一个组件的第二套实现」** | `workbench.js:74-190`：打开时**焦点进面板**（`:110`）、关闭后**焦点回开关**（`:117`）、**原生 select 留在 DOM** 承载值（`:124`） | **必须并入**统一的 `.lk-select`（`design.md` D-1.8 · `tasks.md` 2.8），否则仓库里会留下两套实现 |

### 既有契约（本 change **不得**改写它们）

| 契约 | 出处 | 本 change 的关系 |
|---|---|---|
| `Provider activity cards show evidenced outcomes` | `openspec/specs/workbench-ui/spec.md:1384` | **不冲突**：本 change 只改**形态**，不改「有证据才说影响、未知就说未知、诊断默认折叠、摘要 ≤240 字」 |
| `Failed activities expose a concise error summary` | 同上 `:922` | **不冲突**：失败摘要仍 ≤240 字、不展开即可读 |
| `Pi activities are conversation messages` | 同上 `:853` | **不冲突**：按活动 id 原地更新、不产生重复行 |
| `Chapter switch in the top bar` | 同上 `:829` | **不冲突**：章节透镜**不得显示 per-chapter 计数** |
| `Focus visibility and contrast floors` | 同上 `:435` | **继承**：焦点环不被压死、对比度门槛 |
| `Consecutive-correct escalation feedback` | v2 **待归档** delta | ⚠️ **并行协调**：它说「连对进度是逐簇点亮的指示器」——本 change 的 4.16 把这个指示器**定形**为编号点串；两处需协调（见 Impact） |

---

## What Changes

> **四条共用的纪律**：每条都写清「**变的是什么**」与「**不变的是什么**」；
> 「不变」那半边与「变」的那半边同等重要——它们是**验收时用来判红的红线**。

### 一、§4.7 自绘下拉（`select-spec`）

**变的是什么（新增的用户可观察行为）**

1. **8 处原生 `<select>` 换成自绘控件**：触发器 + 浮起面板 + 选中项蓝洗底 + 行尾蓝点。
2. **键盘模型**：↑↓ 移动、Home/End 到首末、Enter/Space 选中、**Esc 关闭且不改值**、
   输入字母做首字母跳转。
3. **ARIA 角色**：触发器 `combobox`（带 expanded / controls / activedescendant）·
   面板 `listbox` · 选项 `option`（带 selected）。
4. **焦点模型**：**打开时焦点留在触发器**（不新增 Tab 停靠点）· **关闭后焦点回到触发器**。
5. **无脚本回落**：原生 `<select>` 仍然给出同样的选项、报同样的值。

**不变的是什么（红线）**

- ⚠️ **载荷仍由 hidden input 承载**；请求的**方法 / 路径 / 载荷键集合逐条不变**（**G-1**）。
- 每个控件的**选项集合与选项值不变**（尤其章节透镜**不显示每章计数**）。
- 控件**占一个 Tab 停靠点**，页面既有 Tab 顺序**不被打乱**（**G-8**）。
- 命中区 ≥ 44×44 CSS px；焦点环不得被压死；reduced-motion 降级规则不变。

### 二、§4.16 分段进度条（`steps-num`）

**变的是什么**

1. **一个全新界面**：编号圆点 + 连接线（「第几轮」一眼可数）。
2. **状态用形状 + 颜色双编码**：已完成 / 当前 / 未开始 / 失败。
3. **段数超限**时折叠为紧凑摘要（仍说清「完成几个、共几个」）。
4. **它不是控件**：不进 Tab 序列、不改任何值、不发任何请求。

**不变的是什么**

- 数字**只取周围界面已有的值**；**不新增统计 / 比率 / 分数**；**不写池**。
- 连对语义、连对的档位与横幅契约**不变**（v2 `Consecutive-correct escalation feedback`）。
- 状态**不得只靠颜色**（既有 `Redundant state cues` 仍然成立）。

### 三、§4.24 对话框（`dialog-spec`）

**变的是什么**

1. **一个真正的模态**：暖墨面纱遮罩 + 浮起面板 + 右对齐动作区。
2. **Esc 关闭** · **Tab 焦点陷阱**（面板内循环，不跑到背后）·
   **焦点归还到触发元素**（触发元素已消失时落到它所在的区域，**不得留在 body 上**）。
3. **遮罩点击不关闭** —— 关闭必须是显式动作（面板内按钮或 Esc）。
4. **失败就地报告**：面板不关、标 busy、焦点留在面板内。
5. **6 处原生 `window.confirm()` 改用该对话框**（删试卷 / 删目标 / 删做题经验 /
   删本地会话 / 放弃未完成练习 / 整批回滚）。

**不变的是什么**

- **Agent 的内联确认卡仍是内联卡** —— **不变**为模态（它受 Agent 契约管，且不是「打断」）。
- 确认**之前不发请求**、确认**之后才发** —— 与原生 confirm 的语义一致 ⇒
  **请求序列与载荷不变**（G-1）。
- 不写池、不新增持久字段；命中区 / 焦点环 / reduced-motion 规则不变。

### 四、§4.25 工具调用卡（`tool-line`）

**变的是什么**

1. **一个全新形态**：一行摘要 —— 状态点 + 工具名 + 耗时 + 展开箭头。
2. **耗时的取值来源被钉死**：只取活动**自报**的时长；**没有就不显示**，不臆造。
3. **展开 / 收起用真按钮**（`aria-expanded` + `aria-controls`），展开区是
   `region` 且有自己的可访问名 —— 键盘路径从「原生 details」变成可断言的 ARIA 契约。
4. **失败由状态点承担**（不加红字）；≤240 字摘要仍然**不展开即可读**。

**不变的是什么**

- 既有 `Provider activity cards show evidenced outcomes`（`:1384`）与
  `Failed activities expose a concise error summary`（`:922`）的**全部约束**：
  语义动作名 · 真实状态 · 有证据的结果 / 影响 · **未知就如实说未知** ·
  诊断净化后默认折叠 · 摘要 ≤240 字 · **不提供后端不支持的选择性重试**。
- 执行计划（Execution Plan）作为**时间线**的定位不变；Pi 活动**原地更新不重复**的契约不变。
- 不写池、不新增持久字段。

---

## Capabilities

### New Capabilities

- **无。** 四条都落在既有能力 `workbench-ui` 上 —— 它们改的是**同一个工作台里
  同一批控件的形态与行为**，不是一条独立的能力。立新能力会把「同一个组件的两套说法」
  变成「两个能力各说一半」，与本轮「消灭同一组件多个形态」的用意相反。

### Modified Capabilities

- **`workbench-ui`**：**4 条 ADDED Requirements**（无 MODIFIED、无 REMOVED）——
  1. `Custom select replaces the native select`（§4.7）
  2. `Segmented progress shows numbered steps`（§4.16）
  3. `Modal dialog interrupts and owns focus`（§4.24）
  4. `Tool call card is one line`（§4.25）

  **为什么是 ADDED 而不是 MODIFIED**：这四条**不改写**任何既有需求的**行为**，
  只**新增**此前没有任何界面承载的行为。既有的
  `Provider activity cards show evidenced outcomes` / `Failed activities expose a concise
  error summary` / `Pi activities are conversation messages` / `Chapter switch in the top bar`
  在本 delta 落地后**逐字继续成立** ⇒ 按 AGENTS.md 的契约协调纪律，
  **不把它们整块复制过来再改写**（那会制造无谓的漂移面）。

  **挂 `workbench-ui` 的理由**：这四条描述的都是工作台界面里**用户能直接看到的行为**
  （选一个值 / 看完成到第几步 / 被一个模态打断 / 看一行工具摘要），
  与既有 `workbench-ui` 的需求同属一个能力面。

- **不动**的能力：`review-workbench`（学习模型与池语义）·
  `ai-teacher-bridge`（Agent 协议与活动事件）· 其余 17 个既有能力 —— **一行不改**。

---

## Impact

### 会改的文件（实现阶段；**本 change 只写文档，现在不动**）

| 文件 | 落点 |
|---|---|
| `workbench/server/pages.py` | 8 处 `<select>` 的替换标记；对话框宿主容器 |
| `workbench/server/static/workbench.css` | 新增 `.lk-select` / `.lk-steps` / `.lk-dialog` / `.lk-tool` 四族规则与它们的夜纸取值 |
| `workbench/server/static/workbench.js` | 自绘下拉的初始化与事件绑定；对话框的打开 / 关闭 / 焦点归还；工具调用卡的渲染 |
| `workbench/server/static/agent-ui.js` | Pi 活动（`.ai-activity`）改用工具调用卡形态；Agent 内联确认卡**保持内联不动** |
| `workbench/server/static/agent-ui.css` | 工具调用卡在对话流里的定位与状态 |
| `workbench/server/static/paper-practice.js` · `practice-flow.js` · `kp-experience.js` | 6 处原生确认改为调用对话框 |

### **不会**改的文件 / 契约（红线）

- **不写池**：`pool/` · `pipeline/` · `workbench/data/` **一行不动**；
  **不新增任何持久字段、不新增任何学习事实、不新增统计行**。
- **不改请求契约**：API 的**方法 / 路径 / 载荷键集合**逐条不变（**G-1**）——
  自绘下拉的载荷仍由 hidden input 承载；对话框的确认前不发请求。
- **不改既有 Agent 契约**：`ai-teacher-bridge` 的活动事件、审批门语义、Artifact 语义一律不动。
- **不改图谱**：知识图谱页**不在本 change 范围内**（归 `graph-node-visual-language`）。
- **不改 `openspec/specs/`**：那是已归档的当前事实，本 change 只在 `openspec/changes/` 里。
- **不改 `docs/GLOSSARY.md`**：本 change 起草时它正被另一波写；需要新建的词条已列出，
  由主会话统一落（见下）。
- **不改另两个 change 的目录**：`workbench-visual-language-v2/` 与
  `graph-node-visual-language/` 是别人的地盘，**本 change 一个字节都不碰**。

### 并行变更的协调点

| 并行项 | 关系 | 处理 |
|---|---|---|
| v2 待归档 delta 的 `Consecutive-correct escalation feedback` | 它说「连对进度是逐簇点亮的指示器」；本 change 的 4.16 把这个指示器**定形**为编号点串 | **归档时协调**：v2 先归档，本 change 的 4.16 在其之上把「指示器」的形态写实；两处措辞需一致（登记在 `design.md` 的待裁决项 T-4） |
| v2 的 `Provider activity cards show evidenced outcomes`（若被 v2 改写） | 4.25 依赖它的「有证据才说影响 / 未知就说未知 / 摘要 ≤240 字」 | 本 change **不复制**该需求，只在 4.25 里**引用**这些约束；归档时复核 v2 版本仍成立 |
| `workbench-component-forms` 与 `graph-node-visual-language` | 都挂在 `workbench-ui` 上 | 两者**不碰同一条需求**（一个动控件，一个动图谱）⇒ 无冲突 |

### 需要新建的 GLOSSARY 词条（本 change **不写** `docs/GLOSSARY.md`，只登记）

见 `design.md` 末尾的「术语登记」一节（词条 / 定义 / 出处，一行一条）。

---

## 与 AGENTS.md 的对齐

| 纪律 | 本 change 的做法 |
|---|---|
| 1 · 需求先落文档再动代码 | 本 change **只写规格**；产品代码一行不动 |
| 2 · 名词先定义后使用 | 新名词**全部登记**待落 `docs/GLOSSARY.md`；本 change 的正文**只用已在 GLOSSARY 的词**（柔和蒙德里安 v2 / 纸面层级 / 冗余状态通道 / 焦点环 / 命中区 / 夜纸 / 执行计划 / 工具调用卡 / 审批门） |
| 3 · 契约协调 | 「不变的是什么」逐条列出；既有需求**不复制不改写**；协调点已登记 |
| 4 · Ponytail 阶梯 | 本 change 不写代码；规格只写**行为**，不写实现步骤 |
| 6 · 验证节奏 | `openspec validate workbench-component-forms --strict` ·
  `openspec validate --specs --strict` · `python -m pytest tests -q` 三条全跑（结果见报告） |
