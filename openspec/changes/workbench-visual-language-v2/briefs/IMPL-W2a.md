# IMPL-W2a — CSS 语言层：共享阅读层 · 动效 token 与分级降级 · 字体声明

> 实现任务：`openspec/changes/workbench-visual-language-v2/tasks.md` 的 **第 6 组（6.1–6.5）**
> · **第 8 组（8.1–8.7）** · **5.3**。
> **只改 `workbench/server/static/workbench.css`**。

## 前置
第 1–4 组的 token 地基**已落地**（Step 1 = 新 token 层 + 旧 token 别名期）。
读 `workbench.css` 的 `:root` 确认**新 token 名已在位**，再动手；不要重复定义。

## 必读
1. `tasks.md` 的 **第 6 组 / 第 8 组 / 5.3**（你的任务书，逐条实现）
2. `design-notes/night-paper-tokens.md`（**token 唯一权威**：§2.3 字号档、§2.6 缓动系数、§2.7 z 序）
3. `design.md` 的 **D-5**（阅读版式）与 **D-7**（动效系统）
4. `decisions.md` 的 **A-2**（动效偏好优先级）、**A-6**（题面字号 17px）、
   **A-27**（动效清单 M-A…M-N）、**A-37**（字体只声明 400）
5. `design-notes/motion-spec.md`（20 条 `@keyframes` 与 19 行交互映射 —— **你的 keyframes 直接照它写**）
6. `design-notes/component-spec.md`（哪些元素属于「阅读面」A 组 / 「界面面」B 组）

## 硬约束
- **只改 `workbench/server/static/workbench.css` 这一个文件。**
  不碰 `pages.py` / `workbench.js` / `records.py` / `practice-flow.js` / `paper-practice.js` /
  `docs/` / `openspec/`（**多个并行 agent 正在改它们**）。
- **不要**改 `tasks.md` 的复选框 —— 回报里逐条列完成的 task id。
- **知识图谱区段 `workbench.css:1497-1884` 与图谱 12 个裸名（`:1505-1518`）一行都不许碰。**
- 无框架 / 无构建 / 无 npm / 无 CDN / 无外部资源。纯 CSS。
- **字体只有 400 一个字重**：`SourceHanSerifSC-SemiBold.woff2` **不存在**，
  **不要**为它写 `@font-face`（`design.md` D-4「体积实测」已记）。

## 6.1–6.4 共享阅读层 `.wb-reading`
- 新建 `.wb-reading`（题面变体 `.wb-reading--stem`），刻度全部用 token：
  正文 17px（`--fs-reading`）/ 行高 1.75 / measure 38em（`--measure`）/ 段距 0.7em /
  `text-align: start`（**不 justify**）/ h2·h3·h4 = 22·19·17px 且行高 1.35；
  **自带 h1–h4 规则**（h1 = 24px 仅兜底）——
  这是为了消除 `h3 16px < h4 17px` 的层级倒挂（**第 7 组已把两侧 `###` 都映射成 h4，
  倒挂现在会同时显形**）。
- 六处挂载点（阅读面 A 组）：`.practice-question-card`（现 `workbench.css:924-932`）·
  `.knowledge-body`（`:493-500`）· `.practice-solution`（`:933-940`）·
  `.linked-problem-text`（`:524`）· `.record-answer`（`:1467`）· Agent 长文（`:752`）。
  界面面（h1/h2/h3、导航、按钮、表格、选项控件、状态标签、统计数字、自评星级、元信息、
  空态与错误文案、题号）**一律留在 `--font-ui`**；**标题一律无衬线**。
- `.rich-text` **整体退役**（不保留别名、不并行两套规则）——它与阅读层逐项冲突，
  两者**不得同挂一个元素**。
- 密度分区：阅读面宽松（段间 0.7em 留白，**不用分隔线**）；列表 / 数据面紧凑。

## 8.1–8.7 动效系统
- 动效 token：五档时长 `--dur-fast 120ms` / `--dur-base 160ms` / `--dur-slow 240ms` /
  `--dur-scene 400ms` / `--dur-ceremony 700ms`；
  三档缓动（**系数按权威表 §2.6**）`--ease-out cubic-bezier(.22,.61,.36,1)` /
  `--ease-standard cubic-bezier(.4,0,.2,1)` / `--ease-rebound cubic-bezier(.34,1.3,.64,1)`。
  把现有散落 transition（100/160/180/200/300ms 五档 + 3 种自定义缓动）收编到 token。
- **分级降级**（A-2）：把既有全局降级闸门（`workbench.css:733` 与 `:1126-1131` 的
  `transition:none !important; animation:none !important`）从「一刀切 none」改成**分级降级**：
  系统 reduce + 偏好未设 ⇒ 弱动效档（只允许透明度变化与状态直切；
  禁台灯涟漪 / 彩带纸片 / 挤压回弹 / 入场上浮位移 / 骨架微光扫过）；
  显式「开」⇒ 恢复完整动效；显式「关」⇒ 全部直切。
  ⚠️ **铁律：降级后的终态必须仍然可见** —— 动效的**静态样式必须等于终态**，
  起始态（如 `opacity: 0`）**只能写在 `@keyframes` 内部**。
  否则元素会永远停在「从未出现」的起始态（这是全局 `animation:none !important` 兜底的固有陷阱）。
- 照 `motion-spec.md` 落 20 条 `@keyframes` 与交互映射（只用 transform / opacity）。
- **台灯转场四段**（M-L）：探出 → 点亮 → 涟漪 → 收回，~700ms；
  涟漪层是**底色层**，`z-index: 0`（**在内容之下**，A-1：不得压平卡片），
  内容层 `z-index ≥ 1`；暖光用 `mix-blend-mode: screen`（掉帧则退化 `normal` + 降不透明度）。
  涟漪层承载**目标主题**的 `--surface-base`（由 JS 在转场**开始时**写入，不是结束时）。

## 5.3 字体声明
- `workbench.css` 顶部（`:root` **之前**）声明 `@font-face`：
  `font-display: swap`（**不用** KaTeX 的 `block`，见 `static/katex/katex.min.css:1`）、
  `unicode-range` 限中文。
- 三族分工：`--font-ui` 沿用现有栈（仅改名）· `--font-read` = 衬线栈 ·
  `--font-mono` = 现状 + 补 `monospace` 兜底。
- 字体未加载时先显示 fallback 的**可读文字**（不许空白页）。

## 验证
- 每组末尾跑 AGENTS.md 四条验证命令。
- `file://` 与 http **两种方式**都实测（Chrome 在 `file://` 下会拦外链 SVG 引用）。
- 截图走查：题面 / 知识点正文 / 解析 三处的字号、行高、行宽、字族与标题层级；
  **h3 19px > h4 17px** 必须成立；`grep -rn "rich-text" workbench/` 归零。

## 落盘纪律与回报
2 分钟内先落 `.wb-reading` 骨架，再逐项推进。**每写完一节重写整份文件**（这个文件同时有别人在改，
但只你改 CSS 时它属于你；若发现文件里有你没写过的改动，**停下来报告**）。
最终回报必须复述：**已落盘路径 + 完成的 task id 列表** + **`.wb-reading` 六处挂载点的实测值**
（正文 17px / 29.75px / 38em、h3 19 > h4 17）· **降级四组合的对照帧路径** ·
**`rich-text` 归零的 grep 输出** + **台灯转场四段的时序** + 四条验证命令结果 + 待裁决项。