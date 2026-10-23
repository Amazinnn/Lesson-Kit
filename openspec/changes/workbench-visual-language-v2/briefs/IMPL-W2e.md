# IMPL-W2e — CSS 收口之二：把「标记已实现、样式没跟上」那一批补齐

> 服务于 `openspec/changes/workbench-visual-language-v2/contract-drift.md` **CD-171**
> （+ **A-55 / A-56**）。
> **只改 `workbench/server/static/workbench.css` 这一个文件。**

## 背景（为什么有这一波）
第 28 组做契约同步时发现一批**「标记已实现、样式没跟上」**的东西：
**结构、类名、数据都在，CSS 规则不在** ⇒ 表现为「功能在、界面没接上」。
这些不是契约冲突，是**实现未收口**。本波把它们补齐。

**硬约束**

- **只改 `workbench/server/static/workbench.css` 这一个文件。**
  **绝不改** `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` /
  `middle-navigation.js` / `records.py` / `tests/` / `docs/` / `openspec/` / `tasks.md`
  （**另有几个 agent 正在并行改其中几个**）。
- **不要**改 `tasks.md` 的复选框（主会话统一勾）。
- **知识图谱区段与图谱 12 个裸名一行都不许碰**
  （按选择器定位：`grep -n "Knowledge graph V2" workbench.css`；**不要动图谱页冻结块**）。
- 现有交互逻辑一个字都不许改。
- 动效元素：**起始态只写在 `@keyframes` 内部**（静态样式 = 终态）。
- 只动 `transform` / `opacity` 做动效；状态色一律瞬切。

## 要补的样式（逐条；每条都写明「现在什么样 → 要什么样」）

### 1. 连对计数器三档配色与布局（`.lk-streak` / `.practice-streak` / `.lk-flames`）
- 现在：**这三个类名在 CSS 里零命中** ⇒ 连对计数器**没有配色、没有布局**。
- 要：三级档 **灰 → 黄 → 黄→蓝渐变**（权威表 §3.4 的三角色配额：
  蓝=当前选中/主按钮、黄=当前做得顺/连对进度、灰=中性）。
  ⚠️ **黄色只承载面积与形状**，若计数器里的数字要着色，走 `--role-yellow-deep`。
- 计数器的**几何位置**：常驻练习页的一角（不遮挡题面与导航）；
  数字用 `lk-ticker` 的字族（与界面面同族，**不**用衬线）。
- **档位要能靠颜色之外的方式读出**（冗余状态通道）：火苗簇数 / 字重 / 宽度至少一档变化。

### 2. 火苗簇的**形状**（`.lk-flame` / `.lk-flame-off` / `.lk-flame-on`）—— **最刺眼的一条**
- 现在：只有定位与透明度，**没有底色或图形 ⇒ 火苗完全不可见**。
- 要：火苗是**内联 SVG 或纯 CSS 形状**（两者选一，但**必须可见**）：
  灰层常显 + 黄层随 `is-lit` 交叉淡入（**只动 `opacity`**，不用颜色过渡 —— 动效红线）。
  形状语言对齐第 9 组资产的**写意线稿淡彩**（同一套线宽与圆角）。
  ⚠️ 逐簇点亮靠 `animation-delay`（JS 已写），**你只给形状与两层的显隐规则**。
- 形状要**小而可辨**（火苗簇最多 10 簇 ⇒ 每簇几像素，不能糊成一团）。

### 3. 断裂负反馈的类规则（`.lk-error-nudge`）
- 现在：**只有 `@keyframes lk-error-nudge`，没有 `.lk-error-nudge` 类规则**
  ⇒ JS 只能用内联 `animation` 兜底。
- 要：补上类规则（水平摆动 ≤4px / 160ms 内结束 / **不做屏幕级震动**），
  并让 JS 的内联兜底可以省掉（**你只补 CSS，JS 侧由主会话安排**）。

### 4. 完成页统计数字槽排版（`.lk-stat` / `.lk-stat__value` / `.lk-stat__label`）
- 现在：零命中 ⇒ 完成页那五个数字**没有排版**。
- 要：数字用**界面字族**（`--font-ui`）、较大字号、**tabular-nums**（滚动时不跳宽）；
  标签用次级墨（`--ink-muted`）+ 小字；槽位横向排布，**不遮挡 CTA**。

### 5. 里程碑锚点容器（`.lk-celebrate-anchor`）
- 现在：零命中 ⇒ JS 只能内联写 `position:absolute; inset:0; pointer-events:none`。
- 要：补类规则（绝对定位 + 铺满 + `pointer-events: none` + `aria-hidden`），
  JS 侧的内联兜底可省（**你只补 CSS**）。

### 6. 作答区沉底块与标签（`.paper-answer-block` / `.paper-answer-label`）
- 现在：这两个类名在 CSS 里**零命中** ⇒「你的作答」是**默认字号的裸文字**，
  作答区**没有沉底块**。
- 要：**沉底块**（`--surface-sunken`）+ **12px 圆角** + **1px 内发丝线**
  （`box-shadow: inset 0 0 0 1px var(--rule-hair)`，**不用 border**、不改盒模型）+ **不带柔影**（凹层）；
  标签**16px**（题面内非 stem 文字降一档）+ 次级墨。

### 7. 题面的大号题号（24px）
- 任务 16.1 要求「题号做成 **24px 大数字**（像书的章节号）」。
  ⚠️ 题号**不在** `#paper-question` 里（槽位在它之外，W3b 的 markup 已就位）⇒
  **先 grep `pages.py` 找到题号槽位的实际类名**，再给样式；**不要自己发明类名**。
  若 markup 里**没有**对应类名，**在回报里写明「缺类名，需要 markup 侧配合」**，不要硬写一个对不上的规则。

### 8. 知识点状态圆点（`lk-dot` / `lk-dot--red` / `lk-dot--yellow` / `lk-dot--ink` + `--cross`/`--dash`/`--check`）
- 18.2 的 markup 已用这些类名（`pages.py` 的 `_STATE_DOTS`）。
  ⚠️ **先 grep CSS 里有没有**；若没有 ⇒ 补：
  圆点**颜色 + 几何形状**双通道（红叉 / 黄横杠 / 墨勾），
  形状用 **纯 CSS**（`::before` / `::after` + `border` + `transform`），
  ⚠️ **形状不能靠颜色区分**（灰度下也要可辨）。

### 9. 章节计数条（`knowledge-count-bar`）
- 18.5 的 markup 已落地（`pages.py`）。
  ⚠️ **先 grep CSS**；若没有 ⇒ 补：一条**低调的计数条**（不是新卡片、不是百分比），
  数字用界面字族 + tabular-nums，**不得**出现任何百分比。

### 10. 活动日历的 `.level-0` 档 + 格子高度编码
- 现在：CSS 只有 `.level-1..4`，**没有 `.level-0`** ⇒ 「0 次」这一档靠基础底色兜底，
  **不是设计出来的档**（spec 28.5 要求「0 次有自己的层级、不回落底色」）。
- 要：补 `.level-0`（**要有明确可辨的一档**，颜色更淡但**不是**底色本身）。
- **格子高度**：spec 要求 **fill + height 双编码**（服务端在改，`records.py` 的 agent 正在跑）⇒
  你只需给**高度编码留好承载**：若服务端用行内 `height`/`transform: scaleY`，CSS 侧
  给出 `.record-activity-day` 的**高度锚点**与 `transform-origin: bottom`；
  **不要**自己发明服务端类名 —— **在回报里写清「服务端会用什么类名 / 行内属性，你这边需要什么」**。

### 11. 档位图例的类名（**规范口径，由你定**）
- 服务端（`records.py`）正在被另一个 agent 改，它会输出图例 markup。
  ⇒ **你定一套规范类名**并在回报里写明，让主会话转达给对方：
  - `.lk-legend`（图例容器）
  - `.lk-legend__item`（一项）
  - `.lk-legend__swatch`（色块，**用 `data-level` 挂 `.level-0..4`**）
  - `.lk-legend__range`（区间刻度文字，如「2–3」）
  样式：一行或两行、**低调**、色块与日历格子**同色**（靠 `--level-*` 或 `.level-N` 复用同一取值）。

### 12. A-55：三条轨道去描边
`.record-rating-track` / `.record-verdict-dist-track` / `.record-run-progress`
仍带 `border: 1px solid var(--ink-strong)` ⇒ 按 D-2 改成
**沉底 + 1px 内发丝线**（`box-shadow: inset 0 0 0 1px var(--rule-hair)`，**不改盒模型**）。
**两族一次性改**，别只改一族。

### 13. A-56：判定三态统一走「结构块」
现在「对」= 透明底 + 内发丝墨线块，「错」= 红洗底药丸，「未判定」= 淡墨药丸
⇒ **三态统一走同一个结构块形状**（同一形状/尺寸/内发丝线），
**颜色只承载语义**（`--ink-strong` / `--role-red-ink` / `--ink-faint`）。
⇒ 灰度下靠形状与位置仍可区分。

## 验证
```bash
python -m pytest tests -q
python -m compileall -q lessonkit.py workbench pipeline pool tests
openspec validate --specs --strict
python lessonkit.py guard extract-problems --course dmath --chapter ch06
node tools/graph-layout-diff.js --diff tools/graph-baseline/baseline.json   # 必须 0 条差异
```
- **逐条对照上面 13 条，每条给出「grep 证据 + 截图」**。
- **图谱页零变化**：改完后图谱区段**逐字节不变**（自己 `diff` 一下），
  且 R-2 口径（画布区）仍为 0 差异像素。
- 走查服务按 **A-39**：仓库根为 cwd、**独立端口**（**不要 3081 / 3092 / 3099 / 3411**）、
  池副本 + 隔离注册表；启动后比对服务字节数与磁盘字节数**必须相等**。
  ⚠️ 本机 3099 有**残留 python 进程**，`SO_REUSEADDR` 探测会误报端口空闲 —— 避开它。

## 落盘纪律与回报
- **小步提交**：**一条主题一个 commit**（13 条 ⇒ 13 个 commit 左右），
  只 `git add workbench/server/static/workbench.css`，**不要 `git add -A`**。
- **不要**改 `tasks.md` 的复选框。
- 最终回报（中文）必须复述：已落盘路径 + 每个 commit 的内容 +
**13 条逐条的「改前 → 改后 + 证据」对照表** +
**你定下的图例类名清单** + **你发现的 markup 侧缺口（类名对不上、缺类名等，逐条）** +
**图谱区段逐字节未变的证据** + 四条验证命令结果 + **留给 JS / markup 侧的动作清单** +
**待裁决项**。
- 数字一律以**当场跑出来的命令输出**为准。
