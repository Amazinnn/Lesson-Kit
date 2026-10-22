# IMPL-W2c — CSS 版式层：夜纸值集复测 · 三栏几何单一真值 · 标志带与中栏版式 · 顶栏

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的
> **第 12 组（12.1–12.6）** · **第 13 组（13.1–13.4）** · **第 14 组（14.1–14.4）** · **第 15 组（15.1–15.4）**。
> **只改 `workbench/server/static/workbench.css`**。

## 前置
- 第 1–4 组（token 地基 + 别名期 + 纸面层级 + 色彩收编）**已落地**。
- 第 6 / 8 组（阅读层 `.wb-reading` + 动效 token 与分级降级）由**前一个 agent** 落地。
  ⚠️ **你必须在动手前先读 `workbench.css` 现状**，确认前一个 agent 的改动已在位、
  以及 `:root` 与 `:root[data-theme="night"]` 两套值是否已就位。
  **若发现文件里有你没写过的改动 —— 那是正常的（前一个 agent 的），但若它正在被修改，停下报告。**
- 权威值一律查 `design-notes/night-paper-tokens.md`（§2 结构 / §3 值 / §4 对比度实测）。

> 🔴 **CSS 行号锚点已全部位移** —— 第 1–4 组在 `workbench.css` 的 `:root` 里插入了 318 行，
> 该文件以下所有行号全部位移（且不均匀：+307 / +310 / +702，甚至 −100 / −127）。
> **本任务书里的 `workbench.css:NNNN` 引用全部过期。**
> **一律按选择器 / 声明 / 注释文本现场定位**（`grep -n "<选择器>" workbench/server/static/workbench.css`），
> 交叉核对用 `briefs/ANCHOR-REMAP.md`。
## 硬约束
- **只改 `workbench/server/static/workbench.css` 这一个文件。**
  不碰 `pages.py` / `workbench.js` / `app.py` / `records.py` / `docs/` / `openspec/`
  （**多个并行 agent 正在改它们**）。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **知识图谱区段与图谱 12 个裸名（`--paper` / `--ink` / `--hair` / `--blue` / `--yellow` /
  `--red` / `--shadow` / `--graphite` / `--green` / `--blueSoft` / `--yellowSoft` / `--redSoft`）
  一行都不许碰。**按选择器定位**（`grep -n "Knowledge graph V2" workbench.css` 找边界）。
  本变更**不做暗色下的图谱**（A-8）—— 夜纸下的图谱适配归 `graph-node-visual-language` change。
- ⚠️ **本波不要删别名定义（任务 2.3）** —— 另外三个 agent 正在把
  `pages.py` / `workbench.js` / `practice-flow.js` / `paper-practice.js` 里的
  `.rich-text` 挂载点迁到 `.wb-reading`；**`.rich-text` 的 CSS 规则本波保留**，
  等所有挂载点迁完的那一波统一删（口径见 `decisions.md` **A-41**）。
  同理，**旧的 `--lk-*` / `--dsw-*` 别名定义本波保留**（2.3 留给下一波）。
- 无框架 / 无构建 / 无 npm / 无 CDN。

## 12.1–12.3 夜纸值集与对比度复测
- 确认 `:root[data-theme="night"]` 两套值齐全（表面 4 层 + 墨阶 5 级 + 三角色 11 个 +
  `--rule-control` 等），取值 = 权威表 §3。
  夜纸**只是同一套三角色的第二套值**，**不是新色系**。
- 夜纸下的资产处理：**圆底图标降饱和 + 提亮**；渐变换更暗色阶与更弱高光；
  插画与图标用**同一套 SVG 换变量**，不另画一份。**资产文件数不变。**
- **对比度复测并出表**（逐项重测 `design.md` D-3 / D-12 的表）：
  正文 ≥4.5:1、次要文字 ≥4.5:1、控件边界与非文本状态标记 ≥3:1，**两套主题各测一遍**。
  黄色填充在两主题下都**只承载面积与形状**。
  用可复现的脚本（WCAG 相对亮度公式），把脚本用法写进报告。
- **12.5 台灯涟漪在夜纸下**：涟漪层承载**目标主题**的 `--surface-base`
  （切夜纸 ⇒ `#1c1a16`，切回暖纸 ⇒ `#fdf8ef`），由 JS 在转场**开始时**写入
  （不是结束时 —— 否则会「旧色闪一帧」）；涟漪层与暖光层 `z-index: 0`（**底色层**），
  三栏与卡片 `z-index ≥ 1`（A-1：**不得压平卡片**）；暖光 `mix-blend-mode: screen`
  （掉帧则退化 `normal` + 降不透明度）。
  ⚠️ 涟漪层**不得**接到会随主题变的卡面 token 上（否则涟漪结束时底色会跳变）。

## 13.1–13.4 三栏几何单一真值
- **CSS 持有模板，JS 只写两个列宽变量**：
  `#layout { --wb-col-left: 280px; --wb-col-right: 420px;
  grid-template-columns: var(--wb-col-left) minmax(0,1fr) var(--wb-col-right); }`
  变量写在 `#layout` 上（**不是 `:root`**）。
- ⚠️ 现状 `workbench.css:160` 写的 `minmax(0,1fr)` **从不生效** ——
  被 `workbench.js:4587` 每次 inline 覆盖成 `minmax(420px,1fr)`。
  你只改 CSS 侧；**JS 侧由另一个 agent 改**（改成 `setProperty("--wb-col-left"/"--wb-col-right")`、
  `:4580-4582` 清变量、`:4584-4586` 夹取维持中栏 ≥420px、`:4587` 换写法）。
  你的 CSS 侧要**预留这两个变量名**，并把夹取规则写进注释供 JS 侧对齐。
- 区分**两个同名近义 token**：`--shell-measure` = **880px 阅读轨宽**（不是 `--measure` 的
  **38em 行长**）—— 三个 token 禁止合并（A-20-1 / A-21）。
- 删掉 **128px 死预留**（`workbench.css:255` 的 `padding-right:128px` 与退役 scope-tray 的
  死 CSS `:178-234`）。

## 14.1–14.4 标志带与中栏版式
- 标题带的**结构线**改 2px `--rule-structure`；**删掉** `workbench.css:261-270` 那块
  **76×8 装饰黄块**与 `:258` 的 3px 纯黑底线
  （与「去掉试卷卡 5px 黄带」同源 —— 否则黄色被降级成装订线）。
- 880px 轨与 38em 行长之间那 **234px 差 =「有终点的阅读留白」** —— **不能塌**（A-21-4）。

## 15.1–15.4 顶栏导航与顶栏
- 顶栏三段式：品牌 / 当前身份 / 动作区。**机器课程代号不得出现在任何可见文本**
  （`workbench-ui/spec.md:12` 是硬契约）；章节只在透镜里。
- 顶栏高度 **52px 维持现状**（`--shell-topbar-h`，A-21-3）；`layout-spec.md` 草拟的 56px 作废。
- 章节透镜 = **自绘下拉面板**（圆角、弹出面板带阴影与分隔、每项带章节名；**不得显示每章计数/统计/选择理由**
  —— 现行 spec 明文禁止，`decisions.md` 9.4 已删计数）。

## 附加任务（与上面四组同波，一起做完；都是 CSS 侧、都不碰别的文件）

### 附加 1 · 6.1 的 `.wb-reading--stem`（题面变体）
- 第 6 组的阅读层已由前一个 agent 落地，但 **`.wb-reading--stem` 变体没做**
  （`grep -n "wb-reading--stem" workbench.css` 命中 0）⇒ 6.1 因此没勾。
- 规格：`design.md` **D-5** 的 stem 列 —— 字号 17px / 行高 1.75 / 段距 0.7em /
  measure 38em / h2·h3·h4 = 22·19·17px，**与正文档完全相同**。
  ⇒ 题面变体是**同刻度的语义变体**，需要一个可独立挂载的类名。
- ⚠️ 注意：`.rich-text` 的旧规则**与阅读层逐项冲突**（这正是 6.3 要退役它的原因），
  而现在 `.rich-text` 与 `.wb-reading` 已被写成**同值**（前一个 agent 的过渡措施）。
  **你加 `--stem` 时不要顺手删 `.rich-text` 的选择器**（见硬约束）。

### 附加 2 · 3.1 / 3.1b 纸面层级与沉底边界
- **3.1** 四层纸面 token 已在（第 1 组落地）；你要做的是**规则侧**：
  沉底层（`--surface-sunken`）的圆角同为 12px 且**不带柔影**（凹层）；
  **除代码块外，全站不得再出现 `--surface-code`**（内容块一律用沉底）。
  验证：`grep -n -- "--surface-code" workbench.css` 的命中点**只有代码块相关规则**。
- **3.1b** 沉底与卡面靠「**底色差 + 1px 内发丝线**」区分（**不是深色块**）：
  发丝线用 `--rule-hair` 以 `box-shadow: inset 0 0 0 1px …` 落地
  （**不用 `border`**，不改盒模型）。
  验证：作答区 / 用户消息与所在卡面**一眼可分**（两主题各截一处）。

### 附加 3 · `--lk-ripple-base` 必须改名
- 第 8 组新造了钩子变量 `--lk-ripple-base`（`background: var(--lk-ripple-base, var(--surface-base))`），
  但它落在 **`--lk-*` 家族**里 ⇒ 会**卡住任务 2.3 的验收**（「非图谱区 `--lk-` / `--dsw-` 归零」）。
- ⇒ 改名到一个**不与旧别名冲突**的名字（建议 `--ripple-base`），**取值与语义不变**。
  ⚠️ `workbench.js` 侧有一个 agent 正在写这个变量（转场开始时写目标主题底色）——
  **改名会与他的写入端脱节**。因此：**先把新名定下来并写进回报**
  （例如「CSS 用 `--ripple-base`，JS 侧请写 `--ripple-base`」），
  **并在 CSS 里同时保留 `--lk-ripple-base` 作为一个过渡别名**（值相同），
  这样两边的改动不会互相打断。**下一波再删旧名。**

## 验证
- 每组末尾跑 AGENTS.md 四条验证命令。
- **对比度复测表**要作为产物交出（不是「我测过了」）。
- 截图走查：6 类页面的亮 / 暗双主题对照（工作台 / 练习 / 知识点 / 记录 / 试卷 / 设置视图）；
  **图谱页必须逐像素零变化**（G-5 否定式断言）—— 图谱不在本次范围，但**不许被误伤**。
- `file://` 与 http 两种方式都实测。

## 落盘纪律与回报
2 分钟内先落第 12 组（夜纸值集核对 + 对比度复测脚本），再逐组推进。
每写完一节**重写整份文件**；若发现文件里有你没写过的改动，**先确认不是别人正在写**，再决定是否继续。
最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **两主题的对比度复测表** +
**三栏几何的最终数值** + **128px 死预留与 76×8 黄块的删除证据** +
**图谱页逐像素零差异的证据** + 四条验证命令结果 + 待裁决项。