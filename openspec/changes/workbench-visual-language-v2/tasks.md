# Tasks — workbench-visual-language-v2

> **视觉基线唯一依据**：`decisions.md`「# 收口：最终基线」（暖色 + 现代圆润）。
> **实现方案依据**：`design.md` D-1…D-15（token 架构 / 纸面层级 / 色彩收编 / 双字族 /
> 阅读版式 / Markdown 双渲染器 / 动效 / 动效偏好 / 设置视图 / 三栏几何 / 128px 死预留 /
> 焦点与对比度 / 记录中心 / 作答日历 / 契约漂移登记）。
> **行为契约依据**：`specs/workbench-ui/spec.md`（9 ADDED + 9 MODIFIED）、
> `specs/workbench-settings/spec.md`（新能力，7 需求 / 25 场景）、
> `specs/calendar-workload/spec.md`（delta，1 需求 / 14 场景）。
> **验收口径依据**：`acceptance.md`（§0 底线守卫 G-1…G-8、§1 对照截图 S-1…S-12、
> §2 关键帧 M-1…M-13、§3 交互清单、§4 通过标准、§5 走查协议）。
> **补充规格**：`design-notes/asset-spec.md`（SVG 资产规格）、
> `design-notes/motion-spec.md`（动效规格）、`design-notes/component-spec.md`（组件规格）、
> `design-notes/copy-table.md`（全站文案对照表）。
>
> **实施口径**：请求与持久化不变（冻结清单见 `proposal.md`「Frozen」）；本变更只改表现层。
> **交付分两段**：**样板线**（第 1–22 组，用户验收前）与**铺开**（第 23–28 组，样板线验收通过后）。
> 第 22 组是验收关卡，**关卡未过不得启动第 23 组**。
> **分支**：`feat/workbench-visual-language-v2`，不并入 main；每个可验证单元单独提交，
> 提交信息用 `feat/` `fix/` `docs/` `chore/` `refactor/` 前缀，工作区不留脏。
> **硬约束**：无框架、无构建步骤、无 npm、无 CDN、无外部图标字体；纯 CSS + 原生 JS。
> **知识图谱页完全不在范围内**（`decisions.md` **A-8** 裁决，2026-10-22）：本变更**不触碰图谱** ——
> 夜纸下的图谱适配与图谱节点视觉重设计都归独立 change `graph-node-visual-language`；
> 在本变更里先换一遍夜纸值、下个 change 再重画节点，会留下「换了夜纸但节点仍然丑」的半成品。
> 本变更对图谱只负一条**不误伤**的责任：图谱专用区段 `workbench/server/static/workbench.css:1497-1884`
> 及其图谱专用 `:root`（L1505-1518，含 `--paper:#fffdf7`、`--ink:#191816`、`--hair:#ddd8cd`）一行不改；
> 新 token 层不得改变图谱依赖的取值。移交清单见 `design-notes/graph-isolation.md`。
>
> **每组末尾的「阶段验收」任务统一要求跑 AGENTS.md 的四条验证命令**：
> `python -m pytest tests -q`、`python -m compileall -q lessonkit.py workbench pipeline pool tests`、
> `openspec validate --specs --strict`、`python lessonkit.py guard extract-problems --course dmath --chapter ch06`；
> 并按 `acceptance.md` §6 指向对应小节（地基阶段 → §0 + §3.1 + §3.6；样板线阶段 → §1 + §2 + §3 全量；
> 铺开阶段 → §1 中新增页面对应条目 + §3 增补项）；截图走查一律在**池数据库副本 + 隔离注册表 +
> 独立端口**上点检，**永不写真实池**。

---

## 第一段：样板线（token 地基 + 外壳 + 练习页 + 知识点页 + 记录页 + 设置视图）

## 1. token 架构：权威表命名族 + 图谱不受影响 （design.md D-1）

- [x] 1.1 在 `workbench/server/static/workbench.css` 的 `:root`（L4-46）内按**权威表 `design-notes/night-paper-tokens.md` §2 / §3 的命名族**建 token：**结构 token 唯一一套**（`--r-*` / `--sp-*` / `--fs-*` / `--elev-*` / `--dur-*` / `--ease-*` / `--z-*` / `--measure` / `--font-*` / `--fw-*` / `--lw-*`）；三栏几何另用布局族 `--shell-col-left` / `--shell-col-right`（**权威表 §2.8 已收录 `--shell-*` 布局几何族**，A-20-1 / A-21：`--shell-measure` = **880px 轨宽**、`--shell-topbar-h` = **52px 维持现状**；**均不是** `--measure` 的 **38em 行长** —— 三个 token **禁止合并**），**主题值两套**（`--surface-*` / `--ink-*` / `--role-*` / `--rule-*`），随主题整套替换；新 token 与图谱裸名（`--paper / --ink / --hair / --blue / --yellow / --red / --shadow / --graphite / --green / --blueSoft / --yellowSoft / --redSoft`，L1505-1518）**零同名**。验证：新 token 名集合与图谱 12 个裸名求差为空（脚本校验）。⚠️ 这条零同名是**本变更对图谱的唯一硬约束**（`decisions.md` A-8：图谱不在本变更范围内，但新层一旦用了图谱的裸名，图谱画布与详情面板会立刻变色）。
- [x] 1.2 **图谱不受影响（保护措施，不是图谱改造）**：按 `decisions.md` **A-8**，本变更**不触碰图谱** —— 夜纸下的图谱适配与节点视觉重设计归独立 change `graph-node-visual-language`。本条只做一件事：**保证本变更不误伤图谱**（即 `acceptance.md` G-5 那条否定式断言）。落地口径：新层**不重定义**图谱的 12 个裸名（见 1.1），**不借 token 层改写** `--paper` 等图谱变量；图谱页中栏底色由**图谱专用的冻结值**供给（恒 `#fffdf7`、两主题同值），**不得**接到会随主题变的卡面 token 上（该 token 的命名漂移见 `design-notes/graph-isolation.md` §7.3 / Q-6）。验证：图谱页中栏 computed background = `rgb(255, 253, 247)`；图谱页截图逐像素比对差异为 0。移交清单（图谱 change 接手时必须知道的硬事实）见 `design-notes/graph-isolation.md`。
- [x] 1.3 按主题声明 `color-scheme`（亮色 `light` / 夜纸 `dark`），让原生控件与滚动条跟随；主题来源按**所有者裁决 A-11** —— **学习者显式选择优先**，**无已存偏好时**以系统 `prefers-color-scheme` 为默认（全仓 `prefers-color-scheme` 命中 0 处 ⇒ 这是一条**新增**默认，不是要保的既有行为）。验证：`getComputedStyle(document.documentElement).colorScheme` 随主题切换；未设置偏好时跟随系统（系统亮 ⇒ 暖奶油，系统暗 ⇒ 夜纸）；显式选择后不再被系统改变。
- [x] 1.4 固化迁移顺序（design.md Risks 第一条）：Step 1 只换 `:root` 里的值（新增 0 个 class、0 处 JS、0 处结构）→ Step 2 换描边 / 抬升 / 文字灰与 22 个硬编码色 → Step 3 才动间距 / 字号 / 圆角 / 动效 / z-index，且 Step 3 再拆 3a 装饰性间距 → 3b 字号行高 → 3c 圆角 → 3d 容器 padding → 3e 动效 / z-index；每小步单独提交、单独截图。验证：git log 显示这些小步为独立提交；每步后 `python -m pytest tests -q` 与 `python -m compileall -q lessonkit.py workbench pipeline pool tests` 全绿。
- [x] 1.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0 + §3.1 + §3.6 走查（底线守卫前置、本组贡献 G-5 图谱像素比对与 §3.1 焦点可见性、§3.6 资产与圆角语言）；截图走查范围＝工作台 / 练习 / 记录 / **图谱**四页基线比对。

## 2. 旧 token 别名期与未定义变量补齐 （design.md D-1 别名期）

- [x] 2.1 旧 token 走别名期：`--lk-*` 与 `--dsw-*`（L5-45）全部改成指向新 token 的别名（例 `--lk-blue: var(--role-blue)`），**只做值替换、不改任何引用点**；每条别名定义处加注释「别名期，勿新增引用」。验证：别名定义处全部是 `var(--role-*)` / `var(--surface-*)` / `var(--ink-*)` 等权威表 token；`grep -c -- "--lk-\|--dsw-" workbench.css` 的**引用点数**不变；回滚只需把别名定义改回原值（一条提交）。
- [x] 2.2 补齐 4 个从未定义的变量（**单独提交、单独 review、单独截图**）：`--dsw-bg-layer-3`（L858）、`--dsw-border-subtle`（L799）、`--dsw-text-muted`（L1051）、`--dsw-border`（L1464 / L1473 / L1895）。特别注意 `--dsw-border-subtle` 无 fallback → 补齐后表格线会从「正文色」变成新规则色，属可见变化，必须单独确认。验证：`grep -oE "var\(--[a-z0-9-]+" workbench/server/static/workbench.css | sort -u` 中无未定义引用；记录页表格线补齐前后各一张截图。
- [x] 2.3 别名期收尾（**独立提交**）：删除别名定义与引用点；删除前用 `grep -oE "var\(--[a-z-]+" | sort -u` 与新层定义集合求差验证无残留。验证：新层定义集合与被引用集合的差为空；非图谱区 `--dsw-` / `--lk-` 归零。
- [x] 2.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0 走查 G-1…G-8（别名期是回滚保障，必须确认「值替换、不改引用点」成立）；截图走查范围＝全站基色与纸面色差。

## 3. 纸面层级与抬升 （design.md D-2）

- [x] 3.1 落四层纸面 token（取值 = 权威表 §3.1）：底 `--surface-base` #fdf8ef / #1c1a16、卡 `--surface-card` #fffdf7 / #232019、浮起 `--surface-raised` #ffffff / #2b2620、**沉底 `--surface-sunken` #f2ece1 / #272319**（**A-23**：原「墨块」层改为浅底深字的沉底层；内容块——作答区、用户消息、强调块——一律用它）；**近黑面另有 `--surface-code` #221f1a / #14120f（由原 `--surface-ink` 更名，语义收窄为「仅代码块 / 等宽代码区的反白面」，取值不变）**；**一个元素只处于一层**。验证：grep 页面全部 surface 类，卡 / 浮起 / 沉底的 background 各自只对应一个 token；**除代码块外，全站不得再出现 `--surface-code`**（内容块用沉底）；沉底层圆角同为 12px 且**不带柔影**（凹层）。
- [x] 3.1b **A-23：沉底与卡面的边界**（权威表 §3.1【A-23-3】/ §6.3 例外 4）：沉底层**不是深色块**，没有「深色自证」可依赖 → 必须补「**底色差 + 1px 内发丝线**」：底色差实测浅色 ΔL\* 5.73 / 夜纸 1.49，内发丝线用 `--rule-hair`（亮 #e6dcc4 / 夜 #332d25）以 `box-shadow: inset 0 0 0 1px …` 落地（**不用 `border`**，不改盒模型）。验证：作答区 / 用户消息与所在卡面**一眼可分**（两主题各截一处）；`grep -n -- "--surface-code" workbench.css` 的命中点**只有代码块相关规则**。
- [x] 3.2 抬升用**暖调柔影**三档：`--elev-1/2/3` 色基 `rgb(61 52 37 / α)`（权威表 §3.6；夜纸改为明度阶 + 顶光 + 暖辉），替换 `--dsw-shadow-lv1..lv3`（L36-39 的 `rgb(0 0 0 / …)`）；`--elev-1` 第一层 `0 1px 2px` **不得省**（卡 / 底明度差只有 1.04:1，卡片边界完全靠影子读出）。验证：非图谱区 `grep -n "rgb(0 0 0 /"` 归零；卡片边界在 100% 缩放下可辨。
- [x] 3.3 取消描边：56 处 `--dsw-border-l1/l2/l3`（L31-33）引用改为「留白 + 圆角 + 字重」；**唯一保留的发丝线**是控件边界 `--rule-control`（亮 #847552 / 夜 #7d7361）与内容层单侧结构线 `--rule-structure`（亮 #221f1a / 夜 #ece3d3）。验证：`grep -n -- "--dsw-border-l" workbench.css` 归零；输入框 / 下拉框在两主题下都找得到边界（实测 ≥3:1）。
- [x] 3.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.6 + §0 G-5 走查；截图走查范围＝纸面四层的层次关系（底 / 卡 / 浮起 / **沉底**各取一处），确认页面底色为**纯色无纹理无暗角**。

## 4. 色彩收编：三角色配额与墨阶 （design.md D-3）

- [x] 4.1 落角色 token（语义配额不变；取值 = 权威表 §3.4 的 11 个 token）：`--role-blue` #2b62e8 / #7291de、`--role-blue-press` #1f4fc4 / #8fa9e8、`--role-blue-wash` #f2f0ef / #292929、`--role-blue-soft` #e0e3ee / #31343c、`--role-yellow` #f5c518 / #e0c151、`--role-yellow-deep` #8a6a00 / #f0d98a、`--role-yellow-soft` #fcf0cd / #3d3721、`--role-red` #d1392b / #d4736b、`--role-red-ink` #b8331f / #e08878、`--role-red-wash` #f9e9df / #352821、`--role-red-soft` #f6d9d0 / #432f28；`:root` 上方写配额注释（蓝＝主按钮 + 链接 + 当前选中；黄＝当前项 + 复习强调 + 连对进度；红＝失败 + 阻塞）。验证：11 个 token 各一个定义点；新增色相为 0；黄色**只承载面积与形状**，不承载文字（承载语义一律走 `--role-yellow-deep`）。
- [x] 4.2 按 design.md D-3 收编表逐条映射 22 个硬编码色（35 处引用）：`#2864dc`×5 → `--role-blue`、`#57606a`×5 → `--ink-muted`、`#b42318`/`#b62f28` → `--role-red-ink`、`#d12c2c` → `--role-red`、`#d97706`/`#b58b00`/`#e1aa12` → `--role-yellow-deep`、`#e5e7eb` → `--rule-hair`、`#333` → `--ink-body`、`#fff` → `--ink-on-role`、`#111318` → `--ink-strong`、`#fdeceb` → `--role-red-wash`、`#f7f7f4` → `--surface-code`（**代码面**；A-23 更名，原 `--surface-ink`）、`#faf8f2` → `--surface-base`；契约外绿 `#1a7f37` / `#e6f4ea` **在权威表里没有 token 名**（本轮整体移除，见 4.4）。验证：非图谱区硬编码 hex 只剩 token 声明行内的值；`grep -nE "#[0-9a-fA-F]{3,6}" workbench.css` 每处命中都在 token 段内。
- [x] 4.3 墨阶收敛为 **4 级文字灰 + 1 级失活灰**（取值 = 权威表 §3.2）：`--ink-strong` #221f1a / #f4ede0、`--ink-body` #3b3630 / #e7dfd0、`--ink-muted` #6b6459 / #c2b8a5、`--ink-faint` #8d8578 / #978d7c、`--ink-disabled` #8a8275 / #7a7162；把 `--dsw-label-tertiary`（33 处）、`--dsw-label-caption`（5 处）、`--dsw-label-dimmed`（1 处 `::placeholder`）并入 `--ink-faint`，`--dsw-state-warn`（2 处）并入 `--role-yellow-deep`。验证：`--ink-faint` 对暖奶油底 3.45:1、对夜纸底 5.31:1（实测复核，权威表 §4.2 / §4.3；三级文字判定线 ≥3:1）；`::placeholder` 不再靠 fallback `#68707b` 存活；4 级台阶在 100% 缩放下仍可辨。
- [x] 4.4 **契约外绿整体移除 ——「答对」改中性墨 + 勾形几何**：按 `decisions.md` A-20 第 3 条，**答对不再用绿色** ——「答对」= **中性墨 `--ink-strong` + 勾形几何**，「答错」= `--role-red`（既有语义不变）；**不新造绿 token**，权威表 §3.4 仍只收蓝 / 黄 / 红三角色。实现范围 4 处：① `workbench.css:1211` `.micro-verdict.ok` 绿字「判定：正确」→ 中性墨 + 勾形几何；② `workbench.css:1214` `.problem-options label.option-correct` **绿环** → **墨色环 + 勾形标记**；③ `workbench.css:1462` `.record-verdict-ok` 绿底绿字药丸 → 「结构块 + 勾形几何 + 文字」三通道（见 D-13）；④ `workbench.css:1892` `.paper-dot.state-correct` 绿底绿字 → 中性墨 + 勾形几何（见 `component-spec.md` §4.17 题号格）。绑定点同步核对：`paper-practice.js:672`（判定文案）、`practice-flow.js:810`（微测判定）、`practice-flow.js:869`（正确项标记）、`records.py:16,39`（判定徽章）。绿此前是「现状兼容例外」（契约外第四色），登记在第 27 组漂移表（CD-071 / CD-072），**本轮实现时移除，例外不再保留**。验证：`grep -rnE "#1a7f37|#e6f4ea|#d9ebdd|#245d32" workbench/` 归零；练习页正确环 / 记录页判定徽章 / 试卷题号格三处均无绿色像素；「答对」与「答错」在灰度下仍可区分（勾形 vs 红叉 / 红面）；权威表无新增色相。**范围外**：`--dsw-state-success`（`#22c55e`）是 DSH 的 success 态、不表达「答对」，本条不动它。
- [x] 4.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.1（对比度）与 §3.4（红色仅用于失败与阻塞）走查；截图走查范围＝三角色各自的典型承载面（主按钮 / 链接 / 当前选中 / 当前项 / 复习强调 / 失败 / 阻塞）。

## 5. 字体：思源宋体打包与双字族分工 （design.md D-4）

- [x] 5.1 子集化思源宋体：用 `pyftsubset SourceHanSerifSC.otf --unicodes-file=gb2312.txt --flavor=woff2` 产出 `workbench/server/static/fonts/SourceHanSerifSC-Regular.woff2` 与 `SourceHanSerifSC-SemiBold.woff2`（字重 400 / 600），字表覆盖 GB2312 一级字表 3755 + 中文标点 + 数字 + 拉丁 + 常用符号；**必须实测体积**：目标 2 字重合计 ≤ 1.2 MB，实测值回填 `design.md` D-4 的「体积待核」一节；超标时**先砍字重（只留 400）而不是砍字表**。验证：两个 woff2 存在且合计 ≤ 1.2 MB；实测值已写回 design.md；未实测不得勾掉本条。
- [x] 5.2 随字体入库许可与说明：`workbench/server/static/fonts/LICENSE-OFL.txt`（SIL Open Font License 1.1 全文）与 `README.md`（来源版本 + 子集化命令 + 字表清单）。验证：许可文件写明 SIL OFL；README 里的命令行可直接复跑。
- [x] 5.3 `@font-face` 与三族分工：在 `workbench.css` 顶部（`:root` **之前**）声明 `@font-face`，`font-display: swap`（**不用** KaTeX 的 `block`，见 `static/katex/katex.min.css:1`）、`unicode-range` 限中文；`--font-ui` 沿用现有栈（L11-13，仅改名）、`--font-read` = `"Source Han Serif SC","Noto Serif CJK SC","Songti SC","SimSun",serif`、`--font-mono` = 现状 L14-15 **补 `monospace` 兜底**。验证：computed family 在阅读面＝衬线族、界面＝无衬线族、代码＝等宽族，三族互不混用；字体未加载时先显示 fallback 的可读文字（无空白页）。
- [x] 5.4 字体资源缓存策略：字体文件用内容哈希或长 max-age + 版本化 URL（`workbench/server/app.py` 的 `_send_static`；`CONTENT_TYPES` L26-34 已含 `.woff2` / `.woff`）；改 CSS 或字体必须立刻到达用户。验证：改字体后重开浏览器立即生效（`curl -I` 见正确 `Cache-Control` 与 `font/woff2` MIME）；截图里字体未加载（fallback）能被识别，不会被误判为设计问题。
- [ ] 5.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.7（首次加载无字体闪烁）走查；截图走查范围＝阅读面 / 界面 / 代码三处字族与一段含生僻字的教材正文（验证 fallback 时两种字形并存可接受）。

## 6. 共享阅读版式层 `.wb-reading` （design.md D-5）

- [x] 6.1 新建共享阅读版式层 `.wb-reading`（题面变体 `.wb-reading--stem`），刻度全部用 token：正文 17px（`--fs-reading`）/ 行高 1.75 / measure 38em（`--measure`）/ 段距 0.7em / `text-align: start`（**不 justify**）/ h2·h3·h4 = 22·19·17px 且行高 1.35；**自带 h1–h4 规则**（h1 = 24px 仅兜底），消除 `pages.py:978` 把 `###` 映射成 `<h4>` 而 CSS 无 h4 规则造成的层级倒挂。验证：`.wb-reading h3` computed font-size = 19px > `h4` = 17px；正文 computed 17px / 29.75px / 38em。
- [x] 6.2 表面归属按 A / B 组划分：阅读面（连续阅读 ≥ 3 行）挂 `.wb-reading` —— `.practice-question-card`（L924-932）、`.knowledge-body`（L493-500）、`.practice-solution`（L933-940）、`.linked-problem-text`（L524）、`.record-answer`（L1467）、Agent 长文（L752）；界面面（h1 / h2 / h3、导航、按钮、表格、选项控件、状态标签、统计数字、自评星级、元信息、空态与错误文案、题号）一律留在 `--font-ui`。验证：六处挂载点齐全；界面面 computed family 不含衬线族；**标题一律无衬线**。
- [x] 6.3 `.rich-text` **整体退役**（不保留别名、不并行两套规则）：其现规则 L752-809 与阅读层逐项冲突（`line-height:1.7`、h1/h2/h3 = 21/18/16、p margin 8px、code .92em、`:786` 的 `--dsw-border-subtle` 从未定义导致表格线回落 `currentColor`），因此两者**不得同挂一个元素**。验证：`grep -rn "rich-text" workbench/` 归零；补齐变量后表格线不再回落正文色。
- [x] 6.4 密度分区落地：阅读面宽松（段间用 0.7em 留白，**不用分隔线**）；列表 / 数据面紧凑（行、记录条目、会话条目、选项列表用更小字号与更紧间距）。验证：知识点正文段距实测 ≈11.9px；记录页 20 行高度小于基线。
- [ ] 6.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.1 + §3.4 走查；截图走查范围＝题面 / 知识点正文 / 解析三处的字号、行高、行宽、字族与标题层级。

## 7. Markdown 双渲染器统一与 parity 测试 （design.md D-6）

- [x] 7.1 统一到**服务端语义**：正文 `#` → `<h2>`、`##` → `<h3>`、`###` → `<h4>`（服务端 `pages.py:978` 的 `level = len(heading.group(1)) + 1` 保持不变）；客户端 `workbench.js:443` 的 `<h" + heading[1].length + ">` 改为从 `<h2>` 起步。验证：同一份 Markdown 两侧标题层级一致；客户端不再与页面标题争 h1（兑现 `docs/ARCHITECTURE.md:240`「普通 Paper 题目与知识正文共享主阅读层级」）。
- [x] 7.2 补齐两侧其余差异：服务端代码围栏补 `class='language-xx'`（`pages.py:955` 现在丢掉）；引用块统一用客户端的正则 `^\s*>\s?`（`pages.py:993` 现在用 `line.startswith(">")`，行首空格会漏判）。验证：语料里的「行首带空格的引用」与「带语言标记的代码围栏」两侧输出一致。
- [x] 7.3 **新增测试** `tests/test_markdown_render_parity.py`：用一份覆盖 3 级标题 / 有无语言标记的代码围栏 / 引用 / 有序无序列表 / GFM 表格 / 分隔线 / 行内数学的 Markdown 语料，分别喂 `pages._render_markdown()`（服务端）与 `workbench.js` 的渲染函数（客户端，**经 Node 调用同一份 JS 源**），**断言两侧 HTML 逐字符相等**；语料与断言放 `tests/` 下，**不进产品目录**。验证：`python -m pytest tests/test_markdown_render_parity.py -q` 通过；测试在改造前先红（记录现状差异），改完转绿；不得用「人工同步」代替断言。
- [x] 7.4 无 Node 的退化路径：若 CI 无 Node，改为 Node 单测 + pytest 黄金样本双跑，并把「人工同步」写进 `design.md` 的风险表；parity 不得退化成一次性人工核对。验证：无 Node 环境下测试仍可运行并给出明确失败原因。
- [x] 7.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；截图走查范围＝题面 / 知识点正文 / 解析 / 记录摘录四处同源 Markdown 的排版对照；确认「客户端 `#` → h2」是本变更**唯一让既有可见文字变小**的地方，并在验收截图里单列。

## 8. 动效系统与分级降级 （design.md D-7）

- [x] 8.1 落动效 token：五档时长（权威表 §2.6）`--dur-fast` 120ms / `--dur-base` 160ms / `--dur-slow` 240ms / `--dur-scene` 400ms / `--dur-ceremony` 700ms，三档缓动（曲线系数 = 权威表 §2.6，A-18-4 钉死）`--ease-out` `cubic-bezier(.22,.61,.36,1)` / `--ease-standard` `cubic-bezier(.4,0,.2,1)` / `--ease-rebound` `cubic-bezier(.34,1.3,.64,1)`；把现有散落 transition（100/160/180/200/300ms 五档 + 3 种自定义缓动）收编到 token。验证：`grep -nE "transition:[^;]*[0-9]+ms" workbench.css` 每处都引用 token；交互反馈落在 120–180ms、场景动效落在 240–520ms。
- [x] 8.2 从 `design-notes/motion-spec.md` §3 抄入 `@keyframes` 库：`lk-squash-bounce`（多邻国 5 段关键帧 17 / 33 / 83 / 167 / 217ms，共 517ms）、`lk-rise-in-8` / `lk-rise-in-12`、`lk-skeleton-sweep`、`lk-error-nudge`、`lk-combo-in` / `lk-combo-out`、`lk-flame-ignite`、`lk-progress-fill`、`lk-celebrate-burst`、`lk-confetti-fall`、`lk-flip-roll`、`lk-spin`。验证：CSS 中存在这组 keyframes 且与 motion-spec 逐条一致；squash 含 5 个百分比节点且总时长 517ms。
- [x] 8.3 容器动画优先：`middle-navigation.js` 每次切页整体替换 `#middle-page` 的 innerHTML（L87，`installPageContent` L97），因此进场必须是 `#middle-page` 自身的 animation（切页后由 CSS 自动重放），**不得**靠 JS 给子元素加一次性类名；纯 CSS `nth-child` stagger 与骨架屏同样挂容器。验证：代码中无依赖一次性子元素类名的转场；切页后动画仍播放。
- [x] 8.4 JS 编排只留三处：①统计数字滚动（rAF 写 `textContent`）②连对计数器（写已有计数器的值与 class）③台灯转场（写已存在装饰层的 `transform`）；三处都**不新增节点、不新增事件绑定**。验证：新增 JS 只触碰既有元素的 `textContent` / `style`。
- [x] 8.5 性能红线与黑名单：只动 `transform` / `opacity`；单帧 ≤16ms；同屏合成层 ≤30；`will-change` 只在动画期间加、结束后移除；黑名单＝全局背景 canvas、鼠标跟随、视差、光标辉光、**常驻循环动画**、`transition: all`、用 `width/height/top/left` 做过渡。验证：逐帧录屏确认；grep 无 `transition: all` 与常驻 `infinite` 动画；台灯转场（约 700ms）作为例外预算单独记账。
- [ ] 8.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 走查 M-7（挤压回弹）、M-8（视图转场）、M-9（骨架屏）；截图走查范围＝按钮 hover/active、卡片入场、空态入场三处动效（逐帧截图或录屏）。
- [x] 8.7 **台灯转场的四段实现**（A-27 **M-L**；spec 新 Requirement「Lamp transition carries the theme change」）：在 `workbench/server/static/workbench.css` 落三个 `position: fixed` 装饰层 —— `.lk-lamp`（内联 `assets/illustrations/lamp.svg`，第 9 组产出）、`.lk-ripple`（承载**目标主题**的 `--surface-base`）、`.lk-ripple-glow`（灯下暖光）；三层一律 `pointer-events: none`（底线守卫 G-7）。时序照 `design-notes/motion-spec.md` §3.5 + §4.3：探出 ~180ms → 点亮 → 涟漪扩散 ~450ms → 收回，共 ~700ms（`--dur-ceremony`）。⚠️ **涟漪层取 `--z-base`（0，在内容层之下）**、灯层取 `--z-lamp`（在内容之上）—— **涟漪不得压平卡片**（`decisions.md` A-1）；涟漪只动 `transform: scale()` 与 `opacity`，**不得**动画化 `mask-image` 的渐变半径（那属逐帧重绘，违反动效红线）。验证：切主题时逐帧录屏可见四段齐全；涟漪全程卡片轮廓清晰未被压平；`grep -n "mask-image" workbench.css` 命中处不与任何 `animation` / `transition` 同声明。
- [x] 8.8 **两档庆祝的 keyframes 与数字滚动落地**（A-27 **M-F / M-G**；spec 新 Requirement「Round completion celebration in two tiers」）：把 `design-notes/motion-spec.md` §3.4 / §3.7 的片段抄进 CSS 与 JS —— `lk-progress-fill`（只动 `scaleX`，`transform-origin: left center`）、`lk-celebrate-burst`（圆环扩散 + 淡出）、`lk-confetti-fall`（纸片位移 + 旋转）、`lk-ticker-*` 逐位数字滚动（vanilla rAF，只写 `textContent` 与 `transform`，**不引第三方库**）。⚠️ **日常档不得触发** burst / confetti —— 触发与否由第 17 组的档位判定控制，本条只保证两套片段可用且彼此独立。验证：逐帧录屏确认日常档只出现数字滚动 + 进度带；里程碑档多出爆点与纸片；庆祝作用域内 `grep -n "url(" workbench.css` 无位图引用。
- [x] 8.9 **reduced-motion 终态一致铁律落地**（spec 总则「Motion system and reduced-motion downgrade」补入的终态条款）：把 `workbench.css:1126-1131` 的全局兜底 `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }` 从「一刀切 none」改成**分级降级闸门**（系统 reduce + 偏好未设 ⇒ 弱动效档；系统 reduce + 偏好显式「开」⇒ 覆盖恢复；偏好显式「关」⇒ 全直切），并逐条保证**每个动效元素的静态样式 == 其终态** —— 起始态（`opacity: 0` / 位移 / 缩放）**只写在 `@keyframes` 内部**，不写进基础规则；逐条落 `design-notes/motion-spec.md` §7.2 降级矩阵的终态。验证：每条动效各出一张降级帧，与动效帧的终态**逐像素比对**（数字、进度带、计数器档位、灯与涟漪层、纸片、火苗簇、内容位置均不得停在中间态）；动效作用域内 `grep -n "opacity: *0"` 命中 0。
- [ ] 8.10 阶段验收（补充：新增动效分镜与降级对照）：按 `acceptance.md` §2 的 M-1（台灯转场）、M-2 / M-3（两档庆祝）、M-5 / M-6（连对计数器与火苗簇）、M-8 / M-9（视图转场与骨架屏）各采一条**分镜条**，并各出一张 reduced-motion 降级对照帧；通用判据＝只用 `transform` / `opacity`、降级帧与动效帧**终态一致**。

## 9. 静物 SVG 资产（可独立验收） （design-notes/asset-spec.md + spec「A navigation graphic depicts its target」）

- [x] 9.1 按 `design-notes/asset-spec.md` 产出 5 枚导航图标：`icon-practice.svg`（翻开的书）、`icon-practice-sets.svg`（一叠纸）、`icon-kps.svg`（书签）、`icon-records.svg`（笔记本）、`icon-graph.svg`（节点连线），落在 `workbench/server/static/assets/icons/`；必须是**具象静物**、不是抽象占位形状（图案适配原则），且与背景由同一套视觉规则推导。验证：5 个文件存在；SVG 不含 `<text>`；不外链字体。
- [x] 9.2 按 asset-spec 产出空态静物插画（同一支笔、同一套线宽与圆角语言）：`empty-vase.svg`、`empty-fruit-basket.svg`、`empty-canvas.svg`、`empty-cup.svg`、`empty-books.svg`、`empty-compass.svg`、`empty-globe.svg`、`empty-inkwell.svg`、`empty-pen.svg`、`empty-pencil-cup.svg` 与 `lamp.svg`，落在 `workbench/server/static/assets/illustrations/`；写意线稿 + 淡彩晕染 + 克制高光。验证：文件存在；单文件色值数受限；图形是具象器物而非抽象几何团块；台灯与其它静物同笔触。
- [x] 9.3 圆底只用三角色色（不同功能区对应不同角色色），**深浅两主题共用同一批 SVG 文件**、用 CSS 变量换前景 / 背景色，不另画一套；渐变只允许出现在图标与插画内部，且用一套有限渐变语言（同一方向、同一组色阶）。验证：切夜纸后图标与插画自动反相；资产目录文件数不随主题变化；`grep -n "linear-gradient" workbench.css` 全部落在图标 / 插画作用域内。
- [x] 9.4 阶段验收（SVG 资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.6 走查；截图走查范围＝左栏 5 项图标 + 各类空态插画 + 台灯，在亮 / 暗两主题下的特写；确认资产目录内无构建脚本、无 base64 内联、无外链、无图标字体、无位图。

## 10. 关键反馈音效资产（可独立验收） （specs/workbench-settings「Sound preference」+ decisions 8.3）

- [x] 10.1 四个关键反馈短音效：答对、答错、完成、里程碑，放 `workbench/server/static/assets/audio/`，每条**短于 200ms**；**其它任何表面 / 事件 / 状态变化都不发声**。验证：4 个文件存在且逐个测时长 < 200ms；触发点只有这四处。
- [x] 10.2 绕过浏览器自动播放限制：首次音效必须发生在**一次用户手势之后**（首次交互时解锁音频上下文），并给出控制台不报错的处理路径。验证：首屏加载后不发声且控制台无自动播放告警；首次点击后可发声。
- [x] 10.3 声音偏好联动与 MIME：开关并入第 11 组的「声音」偏好；关闭后**立即生效、无需刷新**，且**不移除任何视觉反馈**（声音不是唯一通道）；在 `workbench/server/app.py` 的 `CONTENT_TYPES`（L26-34）补 `.mp3` / `.ogg`。验证：关闭后四个时刻都不发声、动效与视觉反馈完整；请求音频返回正确 Content-Type。
- [x] 10.4 阶段验收（音效资产独立验收）：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.3 走查；确认音效不进入任何学习事实或持久化路径（无对应 API 调用、池内无新增记录）。
- [x] 10.5 **四个音效的触发点落位**（A-27 **M-N**；spec 新 Requirement「Key feedback audio cues」）：把四个触发点落到具体文件与具体分支 —— 答对 → `practice-flow.js` 的**判定正确**分支（与 `.micro-verdict.ok` / `.option-correct` 同一处）；答错 → 同一分支的**判定错误**侧；完成 → 练习轮次结束、进入完成页的那一次响应（`pages.py:227` 的 `#paper-completion` 对应流程）；里程碑 → 庆祝**进入里程碑档**的那一拍（与 `lk-celebrate-burst` 同拍，`design-notes/motion-spec.md` §3.7 b 行的 400ms）。⚠️ **只在这四处发声** —— 其它任何表面、事件或状态变化（hover、展开、导航、加载）一律不发声。验证：`grep -rn "playCue\|new Audio\|Audio(" workbench/` 的**调用点**恰好 4 处且分别对应上列四个事件；构造答对 / 答错 / 完成 / 里程碑四个场景各录一次音频波形，确认每个场景只触发一条、且没有第五条。
- [x] 10.6 **音效与动效同步 + 静音即时生效**：里程碑音效必须与几何爆点**落在同一拍**（400ms），不得提前于爆点、不得晚于爆点退场；声音偏好关时四个触发点**都不调用播放**，且**不移除任何视觉反馈**（庆祝动效、答对回弹、答错摆动、连对负反馈全部照常）。验证：静音开关切换后**无需刷新**即生效；静音后录屏确认庆祝动效仍完整播放、四个反馈的视觉通道一个不少；音频四波形与动效帧的时间轴对齐。
- [x] 10.7 阶段验收（补充：声音与动效同步）：按 `acceptance.md` §3.3 + §2 **M-13**（关键反馈音效）走查 —— 四个时刻各一条 <200ms、首次音效发生在一次用户手势之后、加载后零发声、静音后零发声且视觉反馈完整；截图 / 录屏走查范围＝答对 / 答错 / 完成 / 里程碑四个时刻的声画对照。

## 11. 工作台设置视图与偏好存储 （design.md D-9 + D-8）

- [x] 11.1 新增中栏「工作台设置视图」：在 `workbench/server/pages.py` 新增 `settings_page()`，在 `workbench/server/app.py` 的 `_send_page`（L234-261）注册 `/w/{name}/settings` 分支；**只承载外观偏好**（主题 / 阅读字面 / 动效 / 声音），**不得**托管任何改变学习行为的控件（既有 spec 把自评开关钉在左栏）。验证：请求该路径返回 200；视图内无行为类控件；按少字原则，每个偏好是一个自带名称与当前值的控件，不加解释性散文。
- [x] 11.2 左栏开关**开与关**：左栏设置区新增一个控制，打开 / 关闭设置视图；关闭后中栏**回到打开前的视图**；既有两项行为偏好（运行中发送方式、练习显示自评，`pages.py:659-668`）**留在左栏原位**，不得搬走（兼容性边界：用户可感知的位置不能无声搬动）。验证：开 → 关后中栏内容与之前一致；左栏两项偏好仍在原位。
- [x] 11.3 偏好存储**复用既有键**：沿用 `wb_settings_<工作区>`（`workbench.js:165` 的 `SETTINGS_KEY`），把四个外观偏好作为**同一 JSON 对象的四个新键**写入，与既有 `showRating`（`workbench.js:188`）、`runningSendAction`（`workbench.js:503`）并列；**不新增 localStorage 键、不落服务端、不写池**。验证：两个工作区各自独立；删掉存储后主题回到**跟随系统**（A-11：显式选择已被删 ⇒ 系统重新成为默认来源）；grep 确认没有新增键名常量。
- [x] 11.4 首屏无 FOUC：主题属性挂 `<html>`（`document.documentElement.dataset.theme = "night" | ""`），在 `pages.py` 的 `_base`（L1096）`<head>` 内、样式表 `<link>` **之前**放一段内联脚本同步读偏好并写 `dataset.theme`；读取顺序按**所有者裁决 A-11** —— **无已存偏好**时读系统 `prefers-color-scheme`（`matchMedia`），**有已存偏好**时读它；两者都写 `<html data-theme>` ⇒ **首屏仍无闪烁**；**无 JS 时降级为亮色**（暖奶油）；学习者显式选择**优先并覆盖系统**。验证：夜纸首帧截图即为夜纸（无浅色闪帧）；系统暗色 + 无已存偏好时首帧即为夜纸；显式选择暖纸后，系统为暗色也仍是暖纸首帧；视口边缘无露白；改主题时所有表面按纸面层级整套换值。
- [x] 11.5 Agent 右栏不重建：设置视图走 `middle-navigation.js` 的同工作区导航路径，`#ai-column` DOM 与 Agent 控制器**保持挂载**（既有 spec「Same-workspace middle navigation preserves the Agent rail」）；开关设置视图后对话是**同一实例**，不丢滚动位置与草稿输入。验证：开关前后对比 `#ai-column` 的同一 DOM 节点与草稿内容；浏览器前进 / 后退同样成立。
- [x] 11.6 动效偏好语义与分级降级：按**所有者裁决 A-2**（`decisions.md`）落地 —— 动效偏好**默认跟随**系统 `prefers-reduced-motion`；**学习者显式选择优先于系统设置**。三种组合：① 系统 reduce + 偏好未设置 ⇒ 降级为**弱动效档**（允许透明度变化与状态直切；禁止台灯涟漪、彩带 / 纸片、挤压回弹、入场上浮位移、骨架微光扫过）；② 系统 reduce + 偏好显式「开」⇒ **覆盖系统**，恢复完整动效；③ 系统允许 + 偏好显式「关」⇒ 全部直切（比系统更严）。实现上把既有全局降级闸门（`workbench.css:733` 与 `:1126-1131` 的 `transition:none !important; animation:none !important`）从「一刀切 none」改成**分级降级**，并保证降级后的终态**仍然可见**（状态永远是文字 / 几何，不是动画）；三处 JS 编排各自 `matchMedia`（参照 `workbench.js:1639`）。⚠️ 两份 spec delta 原先措辞不一致（`workbench-settings` 写「显式选择优先」、`workbench-ui` 写「系统 reduce 即无条件降级」）—— `workbench-ui` 的 delta 已按 A-2 改写为「无显式选择时跟随系统、显式选择优先」，两处现已对齐；该措辞冲突仍登记为漂移项备查（第 27 组）。验证：四种组合（系统 reduce + 偏好未设 / 系统 reduce + 偏好开 / 系统允许 + 偏好未设 / 系统允许 + 偏好关）各出一张降级对照帧；设置视图显示当前**实际生效**的档位（用状态表达，不加说明文字）。
- [x] 11.7 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.2 + §3.3 走查；截图走查范围＝设置视图亮 / 暗两主题；确认整条设置链路**零请求、零池写入**，且切换偏好不改变任何视图内容、列表顺序、计数与调度。

## 12. 夜纸值集与对比度复测 （design.md D-2 夜纸值 + D-3 / D-12 对比度）

- [x] 12.1 落夜纸值集 `:root[data-theme="night"]`（取值 = 权威表 §3）：表面（`--surface-base` #1c1a16 / `--surface-card` #232019 / `--surface-raised` #2b2620 / **`--surface-sunken` #272319**（A-23 沉底层）/ **`--surface-code` #14120f**（A-23 更名，语义 = 仅代码块反白面））、墨阶（§3.2）、三角色（`--role-blue` #7291de、`--role-blue-press` #8fa9e8、`--role-blue-wash` #292929、`--role-blue-soft` #31343c、`--role-yellow` #e0c151、`--role-yellow-deep` #f0d98a、`--role-yellow-soft` #3d3721、`--role-red` #d4736b、`--role-red-ink` #e08878、`--role-red-wash` #352821、`--role-red-soft` #432f28）、控件边界 `--rule-control` #7d7361。验证：切主题后 computed 值全部命中上表；夜纸**只是同一套三角色的第二套值**，不是新色系。
- [x] 12.2 夜纸下的资产处理：圆底图标**降饱和 + 提亮**；渐变换更暗色阶与更弱高光；插画与图标用同一套 SVG 换变量、不另画一份。验证：夜纸下图标与插画可见且不刺眼；资产文件数不变；**本变更不做暗色下的图谱**（夜纸下的图谱适配归 `graph-node-visual-language` change，见 `decisions.md` A-8）。
- [x] 12.3 对比度复测并出表：正文 ≥4.5:1、次要文字 ≥4.5:1、控件边界与非文本状态标记 ≥3:1，两套主题各测一遍，把实测值写成对照表（逐项重测 design.md D-3 与 D-12 的表）。验证：表中无低于阈值项；`--ink-faint` 亮 3.45:1 / 夜 5.31:1 复核通过（权威表 §4.2 / §4.3，三级文字判定线 ≥3:1）；黄色填充在两主题下都**只承载面积与形状**。
- [x] 12.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.2 走查；截图走查范围＝6 类页面的亮 / 暗双主题对照；确认本变更**未改动图谱**（图谱页观感零变化，即 `acceptance.md` G-5 的否定式断言；夜纸下的图谱适配归 `graph-node-visual-language` change，见 `decisions.md` A-8）。
- [x] 12.5 **台灯涟漪在夜纸下的取值与层级检查**（A-27 **M-L** 的夜纸侧；配合第 8 组的 8.7）：涟漪层承载的是**目标主题**的 `--surface-base`（切夜纸 ⇒ `#1c1a16`，切回暖纸 ⇒ `#fdf8ef`），由 JS 在转场**开始时**写入（不是结束时 —— 否则会出现「旧色闪一帧」）；涟漪层与暖光层取 `--z-base`（0），三栏与卡片 z-index ≥ 1（A-1：**不得压平卡片**）；暖光用 `mix-blend-mode: screen`，若 DevTools 显示该层掉帧则退化为 `normal` + 降低暖光不透明度（观感损失可接受）。⚠️ 涟漪层是**底色层**，不得接到会随主题变的卡面 token 上（否则涟漪结束时底色会跳变）。验证：切到夜纸时涟漪前沿的颜色 == 夜纸底色（实测 RGB 一致）；涟漪全程卡片轮廓清晰；暖光层不掉帧；两方向（→夜纸 / →暖纸）各录一次。
- [x] 12.6 阶段验收（补充：夜纸涟漪）：按 `acceptance.md` §2 **M-1**（台灯主题转场）+ §3.2 走查；截图走查范围＝台灯转场在夜纸方向的中间帧 + 终帧，确认终帧与第 8 组 8.7 的四段时序一致、夜纸值集整套换上、涟漪层未压平卡片。

## 13. 三栏几何单一真值 （design.md D-10）

- [x] 13.1 CSS 持有模板：`#layout` 写 `grid-template-columns: var(--shell-col-left, 280px) minmax(0, 1fr) var(--shell-col-right, 420px);`（现 L160），`#layout[data-ai-collapsed]` 用同样变量、右栏置 0（现 L164）；窄屏媒体查询（`workbench.css:1174-1207` 的 `1fr` 规则）**必须保留**。验证：`#layout` 的**基础** grid 模板在 CSS 里只有一处声明；唯一的第二处是 `#layout[data-ai-collapsed]`（右栏折叠态 ⇒ 右列为 0），是合法状态变体。
- [x] 13.2 JS 只写两个数值变量：`workbench.js:4587` 的 `layout.style.gridTemplateColumns = leftWidth + "px minmax(420px, 1fr) " + rightWidth + "px"` 改为 `layout.style.setProperty("--shell-col-left", …)` / `setProperty("--shell-col-right", …)`；窄屏分支（`workbench.js:4580-4582`）**清变量**而不是清整段 inline 样式。验证：`grep -n "gridTemplateColumns" workbench/server/static/workbench.js` 归零。
- [x] 13.3 不变式与拖拽语义不变：「中栏 ≥ 420px」仍由 JS 夹取维持（`workbench.js:4584-4586` 的 `available = clientWidth - middleMinWidth`），CSS 的 `minmax(0, 1fr)` 只是变量未就位时的首帧兜底；拖拽侧栏的行为契约（只改当前页内存列宽、不导航、不持久化）**完全不变**；`#layout.is-resizing` 上关掉 `grid-template-columns` 过渡以免拖拽出现过渡拖影。验证：把右栏拖到最小后中栏仍 ≥420px；刷新后列宽回到默认；1280×800 与 1024×768 两个视口各拖一次并截图，无拖影。
- [ ] 13.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0 G-8（焦点顺序未因改造改变）+ §3.5（四档视口无横向滚动条）走查；截图走查范围＝1280 / 1024 / 768 三档视口下的三栏几何。

## 14. 标题带与中栏版面配平 （design.md D-11）

- [x] 14.1 删 128px 死预留与 scope-tray 死代码：删 `#middle-page > .page-header { padding-right: 128px; }`（L255）、`.scope-tray-*` 整块（L178-234、L1197）、`practice-flow.js:270` 与 `middle-navigation.js:62-66` 对空壳的引用（确认没有 `document.getElementById("scope-tray-…")` 的 null 解引用）。验证：`grep -rn "128px\|scope-tray" workbench/` 归零且页面无 JS 报错；实测 HTML 本就不渲染 scope tray → 属纯死代码，删除不改变可见行为。
- [x] 14.2 中栏重新配平：阅读列上限 800px → **880px**（`--shell-measure`，**轨宽**）且仍居中；标题带与正文**共用同一条上限与对齐线**（现在 `.page-header` 与 `.page-content` 各有一条 `max-width:800px`（L252-253），而 `.hub-page .page-header`（L1109）不在 `#middle-page` 里 → hub 与工作台规格不一致）；阅读 measure 仍由 `.wb-reading` 自己管（`--measure` = **38em，行长**），容器放宽**不会**把正文拉宽。⚠️ `--shell-measure`（**轨的宽**）与 `--measure`（**行的长**）**不是同一个 token、值不同、禁止合并**（A-21-2 / A-21-4：轨 880px 与行长 38em ≈ 646px 之间那 234px 正是「**有终点的阅读留白**」，双轨机制必须保留）。验证：hub 与工作台标题带左右边界对齐；知识点正文行宽仍为 38em。
- [x] 14.3 去掉标题带的装饰黄块与 3px 黑底线：删 `.page-header::after`（L261-270，76×8 黄块）与 `border-bottom: 3px solid var(--lk-ink)`（L258），换成 2px `--rule-structure`。理由与「去掉试卷卡 5px 黄带」同源：黄色是**稀缺语义色**，不能降级成装订线。验证：`grep -n -- "--lk-yellow" workbench.css` 在非图谱区归零；标题带底边为 2px 结构线；标题带旁与下方**没有任何未认领的空白条**。
- [x] 14.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0 G-5 + §1 S-2 走查；截图走查范围＝五类页面的标题带与中栏边距（确认中栏不再被 128px 预留夹住）。

## 15. 左栏导航语法与顶栏三段式 （spec「Three-column shell with navigation」「Redundant state cues」）

- [x] 15.1 左栏导航语法：每项 = 具象静物图标 + 文字（接第 9 组的 5 枚图标），改 `workbench/server/pages.py` 的 `nav_items`（L628-635）。验证：5 个导航项均含图标，且每枚图标**指向它打开的东西**（不是抽象占位形状）。
- [x] 15.2 选中态 = **整行圆角色块**（现为 1px 黑框，`workbench.css:318-321`），并同时保留两个状态通道：活动文字样式 + 蓝色结构内嵌（既有 spec「Redundant state cues」要求活动项同时具备两者）。验证：选中项无边框、整行浅色块、圆角 12px、含蓝色结构内嵌与活动文字样式；其余项不具备。
- [x] 15.3 左栏分区结构：4 个分区加结构分隔、下半截空纸收敛；「优先回看」的标题**不再随内容有无变体**（现在 `rail_label` 随 `actionable` 变），改为稳定标题 + 计数徽标。验证：分区标题恒定，计数随内容变；空白区高度明显收敛。
- [x] 15.4 顶栏改三段式 + 章节透镜自绘下拉：左＝品牌方块 + 名字，中＝当前身份（**工作区名称**；机器课程代号**不得**出现在顶栏），右＝动作（主题切换、设置、其它）；**顶栏高度维持 `--shell-topbar-h: 52px`（A-21-3：本轮不改顶栏高度**，`workbench.css:1185` 的 `top:52px` 不动**）**；章节上下文**只出现在章节透镜控件里**，不在工作区名旁重复；`_chapter_lens`（`pages.py:41-64`）从裸 `<select>` 改为自绘圆角面板（阴影 + 分隔 + 每项显示章节名；**不得显示每章计数 / 统计 / 选择理由** —— 既有 spec「Chapter switch in the top bar」明令，见 `decisions.md` 9.4 修正），并满足 Esc 关闭、焦点归位、`aria-expanded` 同步、点击外部关闭。验证：顶栏三段可辨；顶栏无课程代号；顶栏高仍为 52px；章节只在透镜里出现；面板键盘可达；面板内**无任何每章计数**。
- [ ] 15.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.4（章节透镜是自绘下拉）+ §1 S-2 走查；截图走查范围＝顶栏三段 + 章节面板展开态 + 左栏选中态。

## 16. 练习页版式三件套 （spec「Learning content is the visual anchor」+ D-5）

- [x] 16.1 题面成为**一张独立的纸** + 24px 大号题号：`#paper-question`（`pages.py:216`）从卡片内段落改为独立纸面（比卡片更亮一级 + 淡结构线）；题号做成 24px 大数字（像书的章节号）。验证：题号 computed font-size = 24px；题面与卡片的层级差可辨；题面**不做装饰性阴影强调**。
- [x] 16.2 解析与题面**同级**：`#paper-reference`（L221）改为同规格的另一张纸（不再是灰掉的小脚注），只用小标题区隔。验证：解析与题面处于同一 paper level；解析字号 17px。
- [x] 16.3 作答区成为**独立标记块**：`#paper-answer`（L219）前加淡结构线 + 「你的作答」标签 + **沉底块 `--surface-sunken`**（**A-23**：作答区不再用近黑墨块，改浅底深字；边界靠底色差 + 1px 内发丝线）；题面内的非 stem 文字（来源行与作答标签）**降一档到 16px**，stem 保持阅读字号。验证：题 / 答两段一眼可分；标签与来源行 computed 16px；**作答区与所在卡面一眼可分**（两主题）。
- [x] 16.4 题号导航冗余编码：`#paper-dots`（L215、`workbench.css:1888`）每项加彩色圆点，已答 / 未答 / 不会 / 未判定四态各有**几何形状 + 颜色**（零可见文字）；当前题加非颜色提示（轮廓或等价物）；整板为紧凑圆角块，**不遮挡题面与导航**；题号显示为大号数字。验证：四态在灰度下仍可区分；每点带可访问名（`aria-label`）。
- [x] 16.5 setup 区、完成页与时间安排层级：`#paper-setup`（L203）、`#paper-completion`（L227）、`#practice-planning` + `_daily_plan`（L237）统一到新卡片规格；时间安排降级为可展开的次级信息。验证：三处层级一致；完成页容器可挂第 17 组的数字滚动与进度带。
- [ ] 16.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0 G-1…G-4（请求序列 / 持久化 / 学习投影 / 复习建议不变）+ §1 S-2 / S-3 走查；截图走查范围＝练习全流程（setup → 题面 → 作答 → 解析 → 自评 → 完成页）。
- [x] 16.7 **完成页为分层庆祝预留承载位**（A-27 **M-F / M-G** 的承载侧；配合第 8 组的 8.8 与第 17 组的 17.6 / 17.7）：`#paper-completion`（`pages.py:227`）先具备三处承载位 —— ① **统计数字槽位**（可挂 `lk-ticker` 逐位滚动）；② **进度带**（`.lk-progress` + `.lk-progress__fill`，`transform-origin: left center`，只动 `scaleX`）；③ **里程碑锚点容器**（承载几何爆点与纸片，`pointer-events: none`，**不得覆盖完成页 CTA**）。⚠️ **承载位的静态样式必须等于其终态** —— 数字直接显示最终值、进度带静态为 `scaleX(1)`、爆点与纸片静态不出现；起始态只写在 `@keyframes` 内部（否则降级后元素永远停在「从未出现」的状态，见第 8 组 8.9 与 `design-notes/motion-spec.md` §7.1）。验证：关闭动效时完成页直接显示最终数字与满格进度带、CTA 可点；里程碑锚点容器不覆盖 CTA（点击穿透）。
- [ ] 16.8 阶段验收（补充：完成页承载位）：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §1 **S-3** + §2 **M-2 / M-3** 走查；截图走查范围＝完成页静帧（数字 + 进度带 + CTA 可点）与降级帧（终态与动效帧一致）。

## 17. 连对反馈与分层庆祝 （spec「Motion system」+ decisions 15.3 / 15.4）

- [x] 17.1 三级连对计数器 + 数字滚动 + 进度动效：常驻练习页，档位＝**灰 → 黄 → 黄→蓝渐变**（我们用黄承载「当前做得顺」，对应多邻国的灰 → 绿 → 绿→蓝）；数字用 Ticker 方式滚动（vanilla rAF，只写 `textContent`）；连对进度本身是动效——火苗簇**逐簇点亮**（`lk-flame-ignite`）。验证：三档颜色可辨（**不靠文字**）；簇数随连对数增长；数字滚动不引第三方库。
- [x] 17.2 **一份**参数化横幅：5 连 / 10 连插播同一份横幅，数字用参数化输入切（`design-notes/motion-spec.md` §6 输入表）；横幅只做一份，不是每个数字一份。验证：横幅资产只有一份；两组参数产出不同数字。
- [x] 17.3 连对中断负反馈：连对 **> 4** 时答错**必须**给明确负反馈（`lk-error-nudge` 等），**不得沉默**，并把计数器复位。验证：构造连对 5 次后答错的场景，界面出现明确信号且计数器归零。
- [ ] 17.4 分层庆祝：日常档（至少有一道错）＝完成页入场 + 数字滚动 + 进度带 0→100%，**无**几何爆点与纸片；里程碑档（全对 / 章节首次完成）＝再叠几何爆点 + 彩带 / 纸片飞散。验证：两档表现明显不同；里程碑档不遮挡完成页 CTA；庆祝全部在响应到达后触发，请求时序未变。
- [ ] 17.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 走查 M-2 / M-3 / M-4 / M-5 / M-6 / M-7；截图走查范围＝连对 1 / 3 / 5 / 10 连四个时点 + 里程碑庆祝 + 降级对照帧。
- [ ] 17.6 **里程碑判定两条件落地**（A-27 **M-F / M-G** 的判定侧；spec 新 Requirement「Round completion celebration in two tiers」；**A-29** 裁定）：里程碑档在下列**任一**条件成立时启用 —— ① 本轮**全对**；② **章节首次完成**。⚠️ **只有这两个条件**：原第三条（本轮结果与自己此前的最好成绩相比）按 `decisions.md` **A-29** 从 spec 去掉 —— 它的**比较范围**（跟同一份卷比？同一章？历史所有练习？比什么量？）在既有契约里**不存在**，仓库里也没有可比的现成来源；**不得用任何代理指标近似**（如「比上次做得好」）触发里程碑 —— 那会造出一个口径未定义的新事实。该条已登记为 `contract-drift.md` **CD-164**：待所有者定义比较范围后，再作为**独立条款**补进 spec，实现期**不得自行发明**。两个条件**任一**成立即进里程碑档，不要求同时成立。验证：两个条件各造一个场景均能触发里程碑档；一个普通轮次（有错 + 非章节首完）**不**触发；判定**不新增请求、不写池**（`acceptance.md` G-1 / G-2 / G-6）。
- [ ] 17.7 **几何爆点与彩带 / 纸片的资产与锚点**（A-27 **M-G**；配合第 8 组的 8.8 与第 16 组的 16.7）：纸片用**内联 SVG** 三种小形状（细条 / 圆片 / 三角）+ 写意线稿淡彩语言（与第 9 组的 `assets/illustrations/` **同一支笔、同一套线宽与圆角**），**不用位图、不用图片序列**；几何爆点为圆环扩散 + 淡出；两者都挂在完成页的里程碑锚点容器内（`pointer-events: none`，**不得遮挡 CTA**），**日常档不挂这两样**。⚠️ 渐变只允许出现在图标与插画内部（权威表 §3.3 的插画语言规则），彩带不得用整屏渐变背景。验证：里程碑档逐帧录屏可见爆点与纸片；日常档两者都不出现；纸片 SVG 与 `assets/illustrations/` 同一笔触语言；纸片落在完成页容器内、不出视口、不盖 CTA。
- [x] 17.8 **连对火苗簇的逐簇点亮与熄灭**（A-27 **M-J / M-K**）：火苗为**内联 SVG**（灰 / 黄两层交叉淡入，只动 `opacity`，避免用颜色过渡 —— 动效红线），随连对数**逐簇点亮**；连对断裂时**逐簇熄灭**并给出明确负反馈（`lk-error-nudge`：水平摆动 ≤4px、160ms 内结束、**不做屏幕级震动**），同时计数器复位。⚠️ 火苗簇是**连对进度的几何冗余通道** —— 计数器被滚出视口时，长度仍可读（spec「The run is not carried by the counter alone」）。验证：连对 1 / 3 / 5 / 10 时簇数逐格增长；断裂时簇全灭 + 出现明确负反馈信号 + 计数器归零；负反馈不得只是颜色变化（须有可辨的形状或位置变化）。
- [ ] 17.9 阶段验收（补充：连对与里程碑分镜）：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §2 **M-2 / M-3 / M-4 / M-5 / M-6 / M-11** 各采一条分镜条，并各出一张 reduced-motion 降级对照帧（终态与开启时一致）；截图走查范围＝连对 1 / 3 / 5 / 10 连四个时点 + **两个**里程碑条件各一次 + 一次断裂负反馈。

## 18. 知识点页 （spec「Redundant state cues」+ D-5）

- [x] 18.1 列表改**分组卡片**：按章节或状态分组，每组一个标题 + 组内圆角卡；`data-kp-order` 仍可保持课程顺序排序。验证：分组结构可见；排序控件仍可用。
- [x] 18.2 状态**冗余状态通道**：把 `state_labels`（`pages.py:378` 的「重点练习 / 可以复习」）改为彩色圆点（颜色主通道 + 几何冗余通道，**零可见文字**，圆点带 `aria-label` / `title`）。验证：列表中不再出现状态文字标签；圆点三态可辨且灰度下可区分。
- [x] 18.3 正文阅读层 + **单侧结构线**：知识点正文挂 `.wb-reading`（17px / 1.75 / 38em），保留**单侧结构线 2px**（`docs/PRODUCT-MANUAL.md:129-130` 硬性要求），结构线色改用 `--rule-structure`；正文**不使用装饰性阴影强调**；提醒与关联题目与正文拉开距离。验证：结构线存在且为 2px；正文无 `box-shadow`；`h3 > h4` 不倒挂。
- [x] 18.4 空态与关联题目：知识点列表空态改第 9 组的插画 + 一句 + 满宽主按钮（按钮文案即动作）；关联题目卡统一卡片规格并挂 `.wb-reading`。验证：空态三段齐备；关联题目排版与正文同层。
- [x] 18.5 **5.2b 进度与成就的可见反馈（一）· 章节内的知识点计数**：在**知识点页**（当前章作用域）加一条**计数条**（不是新卡片、不是百分比）：本章节**知识点总数**，以及处于**重点练习 / 可以复习 / 掌握**三态的知识点**个数**。数据源**只用现成读路径**：总数取 `pool.kps(prefix)`，各态计数取 `learning_current_state.state`（`needs_work` / `review` / `mastered`，`workbench/data/pool.py:279-290`）——**不新增统计行、不写池、不改请求序列**。文案用 `docs/GLOSSARY.md`「当前学习状态」条已定义的**状态名**（`needs_work` 重点练习 / `review` 可以复习 / `mastered` 掌握）；⚠️ 该计数条是**状态分布的汇总**，不是逐条的行动提醒 —— 逐条提醒仍只用「重点练习 / 可以复习」、其余保持中性（GLOSSARY「行动提醒」条），此区别须在 `docs/PRODUCT-MANUAL.md` §3.2 / §7.4 说明。⚠️ **不得**出现正确率 / 掌握度 / 完成度百分比（GLOSSARY `_Avoid_`）；⚠️ **不得**在顶栏章节透镜里显示任何每章计数（现行 spec「Chapter switch in the top bar」明令 no per-chapter statistics / counts）。验证：知识点页顶部可见三个计数；三个数字与 `learning_current_state` 逐条核对一致；页面无百分比文案；顶栏章节面板内无任何计数；池中无新增行。
- [ ] 18.6 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 S-4 / S-5 走查；截图走查范围＝知识点列表（分组 + 圆点状态 + 章节计数条）+ 知识点详情（正文排版 + 单侧结构线）。

## 19. 记录中心：卡片流 / 热力日历 / 仪表盘 （design.md D-13 + D-14）

- [x] 19.1 统计区改**仪表盘卡片**（权重不等，一主三辅），各带一个迷你图（趋势线 / 环形）；`_summary_cards`（`records.py:180`）产出的四个汇总数字（作答次数、已完成练习、客观题正确率、平均自评）**取值与口径保持不变**；并补上**跨记录聚合**（按日分布 + 按判定分布）——卡片流拿走了「对齐扫读」，统计区必须还回来。验证：改造前后四个数字逐位相同（验收时逐张比对）；概览页可读出按日与按判定分布；这一条作为记录中心交付的验收项。
- [x] 19.2 作答明细改**圆角卡片流**：`_attempt_rows`（`records.py:9`）从带边框便签（`.record-row` L1457 叠加 `.card` 基类 L447-453）改为圆角小卡（12px、**不描边**、靠留白 + `--elev-1` 分隔）；**六项字段一个不少**：题目 + 评语 + 摘录（题目下第二、三行）、判定（结构块 + 几何符号 + 文字三通道，**不再是绿药丸**；「对」= 中性墨 `--ink-strong` + 勾形几何，「错」= `--role-red`，见 tasks 4.4）、自评（彩色圆点 + 星级形状，零文字标签）、时间（卡片右上角，次级墨）。验证：字段无缺失；页面中无 `<table>` 边框语义；页高落在 5500–6500px 量级。
- [x] 19.3 错题视图改卡片流 + 视图分级：错题视图同样是圆角卡片流（题面 + 错因摘要），与明细同族但视觉重一档；四个视图做视觉分级（这是一个只读历史页）。验证：错题卡摘要可见；页面仍为只读、零新增请求。
- [x] 19.4 **5.2b 进度与成就的可见反馈（二）· 记录中心的累计量与待确认项**：把 5.2b 的「近期进步曲线」落在**记录中心** —— 已有的**已完成练习轮次**（`practice_runs` 表，`records.py:_runs` / `_practice_sets`）与**近 14 天每天的作答次数**（`records.py:_trend` 的 `attempts` 序列）必须在 19.1 的仪表盘卡片与迷你图里**看得见**（迷你趋势线画的就是**每天的作答次数**）。⚠️ **不新增第四类统计**：不画正确率曲线、不显示任何百分比（GLOSSARY `_Avoid_`；「覆盖」的计算公式也未定义）。⚠️ **「连续学习天数」本轮不做**：全仓**无现成数据源**（`workbench/` 下 `streak` / `consecutive` / 连续 命中 0，无字段无查询），按纪律**不发明算法** —— 已登记为待确认漂移（第 27 组 27.2），待口径定义（哪些行为算学习日 / 断一天是否清零 / 跨时区如何取日）后再补。验证：记录中心可见已完成练习轮次与 14 天每日作答次数；迷你图逐日数值与 `_trend` 一致；页面无新增百分比文案；「连续学习天数」这一**概念**不得存在（记录中心侧 0 命中）。⚠️ **注意**：全仓 `grep "streak\|consecutive"` 不再为 0 —— 命中的是**连对计数器**（`practice-flow.js` 的 `streakCount` / `lk-streak`）与**图谱物理核心里的英文注释**，与「连续学习天数」是**两件不同的事**；判定口径以「记录中心产物里没有连续天数统计」为准。
- [ ] 19.5 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 S-6 / S-7 走查；截图走查范围＝记录中心 4 个视图 + 零记录空态。

## 20. 时间视图负荷柱（`calendar-workload`） （specs/calendar-workload delta + D-7）

- [ ] 20.1 14 天负荷柱从共享基线**逐柱错峰 24ms** 生长，只动 `transform` / `opacity`，时长落在交互 / 场景档内；零负荷日**不画柱**、不错位占位，并保留在共享基线上的位置。验证：录帧确认逐柱错峰与基线不变；柱高比例与精确计数一致。
- [x] 20.2 峰值日与重日的双通道表达：峰值日按**形态 + 颜色**区分；重日（达非零日均的两倍）加**几何**冗余通道标记，**不得靠一堆解释文字**；精确数值标在各自柱上方。验证：重日在无色觉条件下仍可识别；数值与柱一一对应。
- [x] 20.3 降级与空态：动效偏好关、或系统 reduced-motion 生效且无显式覆盖时，柱**立即出现在最终高度**，数值、峰值标记与重日标记同时就位（**不得**停在中间高度或缺标记）；空态 = 一句 + 可选非交互静物插画，且**除这一句外不得再加任何注释**。验证：降级帧与动效帧终态一致；空态无额外注释；该视图不重排、不写入、不改任何学习数据。
- [ ] 20.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 M-10 走查；截图走查范围＝时间视图的负荷柱、峰值 / 重日标记、空态。

## 21. 骨架屏与视图转场 （design.md D-7 视图转场）

- [x] 21.1 骨架屏 = **灰块 + 微光扫过**（`lk-skeleton-sweep`）：容器切页前呈骨架、切页后容器动画接管；加载态带 `aria-busy`。验证：切页可见骨架帧且微光位置变化可见；`aria-busy` 存在；**不引 spinner 图标资源**。
- [x] 21.2 空态 / 加载态 / 错误态**三态各有组件**：`.empty-state`（插画 + 一句 + 满宽主按钮）、`.skeleton`、错误块；错误态用红色且**红色仅用于失败与阻塞**。验证：三种状态各有可触发路径与对应渲染。
- [x] 21.3 焦点不被抢走：转场与浮层出现时**不得**抢焦点；装饰层一律 `pointer-events: none`，可交互元素不在装饰层内。验证：切页后焦点仍在原处或落到新页首个可交互元素（按既有行为）；装饰层 pointer-events 检查通过。
- [ ] 21.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §2 M-8 / M-9 + §0 G-7 走查；截图走查范围＝练习 ⇄ 知识点 ⇄ 记录三次客户端换页的中间帧。
- [x] 21.5 **容器级转场的实现约束落地**（A-27 **M-D / M-E**；spec 新 Requirement「View transition and skeleton loading state」）：`middle-navigation.js` 每次切页**整体替换 `#middle-page` 的 innerHTML**（`installPageContent`），因此转场**必须是 `#middle-page` 自身的 animation**（`#middle-page > *` 挂 `lk-rise-in-8` / `lk-rise-in-12`），**不得**靠 JS 给子元素加一次性类名 —— 切页后该类名会被 innerHTML 替换冲掉；骨架屏同样挂容器（`#middle-page` 先呈骨架、内容到位后由容器动画接管），加载态带 `aria-busy`。⚠️ 图谱页的 `#middle-page` 是**全站共用容器**（`pages.py:97`）⇒ 转场作用域**排除图谱页**（`#layout:not([data-page="graph"]) #middle-page > *`，见 `design-notes/graph-isolation.md` F-6），且**不含 `scale`** —— `scale` 会改变 `graphCanvas.getBoundingClientRect()`，导致环境色 canvas 与真实画布错位。验证：切页后动画**仍播放**（不是只在首次加载播放）；`grep -n "classList.add" middle-navigation.js` 无一次性动效类名；进入图谱页时**不**播放上浮淡入，图谱页观感零变化（`acceptance.md` G-5）。
- [x] 21.6 **降级下骨架与内容的终态一致**：reduced-motion 或动效偏好关时，骨架**不扫光**、内容**直接以终态出现**（位置、层级、可点元素与动效版一致）；**不得**停在「骨架永久停留」或「内容半透明」的状态 —— 骨架块的静态样式必须等于「内容已就位」的状态（起始态只写在 `@keyframes` 内，见第 8 组 8.9 与 `design-notes/motion-spec.md` §7.1）。验证：降级帧与动效帧的终态**逐像素一致**（内容区无残留骨架块、无半透明内容）；`aria-busy` 在降级下同样正确置位与复位。
- [ ] 21.7 阶段验收（补充：视图转场与骨架）：跑 AGENTS.md 四条验证命令；按 `acceptance.md` §2 **M-8 / M-9** + §0 **G-7** 走查；截图走查范围＝练习 ⇄ 知识点 ⇄ 记录三次客户端换页的中间帧 + 各自的 reduced-motion 降级对照帧（终态一致）。

## 22. 样板线验收关卡（`acceptance.md` G / S / M） （acceptance.md G-1…G-8 / S-1…S-12 / M-1…M-13）

- [ ] 22.1 **底线守卫 G-1…G-8**：按 `acceptance.md` §0 逐条执行并留证 —— 脚本化跑一遍练习并 diff 请求方法 / 路径 / 载荷键集合；比对池中 `problem_attempts` / `feedback_events` / `practice_runs` 的行数与关键列；比对学习投影与复习建议集合；图谱页像素比对；池 schema 零变更；装饰层 `pointer-events` 检查；改造前后焦点序列对比。**任何一条红即整体 FAIL，不进入后续评审**。
- [ ] 22.2 **对照截图 S-1…S-12**：按 `acceptance.md` §1 产出改造前 / 改造后并排图（基线在 `tmp/frontend-audit/00-baseline-*.png`；S-3 练习进行中 / S-7 作答明细 / S-9 设置视图 / S-10 夜纸 / S-11 窄屏 / S-12 空态 需新建基线）；比对标准＝同尺寸并排，**不得出现「配色被改」「圆角被改」「信息被删」**，文字除文案清理项外逐字一致。
- [ ] 22.3 **关键帧 M-1…M-13**：按 `acceptance.md` §2 每条动效采帧拼分镜条（台灯转场 6 帧、日常庆祝 5 帧、里程碑庆祝 5 帧、连对插播 5 帧、连对计数器 3 档、火苗簇 3 帧、**连对断裂负反馈 4 帧**、挤压回弹 7 帧、视图转场 4 帧、骨架屏 3 帧、数据层 3 帧、**降级分级 4 帧**、**音效波形 4 段**），并各出一张 reduced-motion 降级对照帧；通用判据＝所有动效只用 `transform` / `opacity`。
- [ ] 22.4 **交互清单与关卡提交**：按 `acceptance.md` §3.1–§3.8 逐条勾选（未勾选项逐条列出并说明为何可接受）；把截图组 + 分镜条 + 勾选表 + 未过项清单一并提交所有者；**验收通过前不得启动第 23–28 组**（铺开段）。
- [ ] 22.5 阶段验收：跑 AGENTS.md 四条验证命令（pytest / compileall / `openspec validate --specs --strict` / `guard extract-problems --course dmath --chapter ch06`）并贴输出；确认 `acceptance.md` §4 的四项通过标准全部满足。
- [ ] 22.6 **动效分镜条专项**（`acceptance.md` §2 **M-1…M-13**；A-27.1「mockup 是静态评审件，不能替代分镜条」）：按 §2 的 13 条**逐条**产出分镜条 —— 台灯 6 帧、日常庆祝 5 帧、里程碑庆祝 5 帧、连对插播 5 帧、连对计数器 3 档、火苗簇 3 帧、连对断裂负反馈 4 帧、挤压回弹 7 帧、视图转场 4 帧、骨架屏 3 帧、数据层 3 帧、降级分级 4 帧、音效波形 4 段；每条附一行判据核对结果。⚠️ **缺一条分镜条即视为该动效未实现** —— 不得以静态截图、mockup 或「代码里写了 animation」代替分镜条。验证：分镜条清单与 §2 的 13 行**逐行对应**、无缺项；每条都能看出运动过程（不是同一帧的复制）。
- [ ] 22.7 **每条动效的 reduced-motion 降级对照帧**：为 §2 的每一条动效各出一张降级对照帧，判据＝**终态与开启时一致**（数字、进度带、计数器档位、灯与涟漪层、纸片、火苗簇、内容位置逐项比对，**不得停在中间态**）；四种组合（系统 reduce + 偏好未设 / 系统 reduce + 偏好显式开 / 系统允许 + 偏好未设 / 系统允许 + 偏好关）各出一张；⚠️ **音频不受动效降级影响** —— 声音偏好与动效偏好相互独立，音效仍按声音偏好发声。验证：每条动效的降级帧与动效帧终态逐像素一致；四组偏好 / 系统组合各一张；关闭动效后庆祝音效**仍然播放**（静音时才不播）。
- [ ] 22.8 阶段验收（补充：动效关卡）：把 22.6 的分镜条组与 22.7 的降级对照帧组一并提交；两张表**逐条勾选**，未过项逐条列出并说明为何可接受；**动效分镜条缺一条即整体 FAIL**（与底线守卫同级）；确认动效全程**未改变请求序列、持久化结果与池 schema**（G-1 / G-2 / G-6 复跑一次）。

---

## 第二段：铺开（样板线验收通过后）

## 23. 试卷列表页 （decisions 11.3 / 11.4 + spec「Accent roles stay scarce」）

- [ ] 23.1 试卷列表改**卡片网格**：每张卡显示标题、题数、状态圆点（`practice_sets_page`，`pages.py:484`）。验证：网格布局成立，卡内三要素齐全。
- [ ] 23.2 去掉试卷卡的 **5px 黄带**：现状**每张卡**都顶一条 5px 黄带，把语义黄降级成装订线，且卡片已带阻塞原因时黄色已无信号价值；改用状态圆点承载状态，让黄色回到稀缺语义色。验证：该黄带规则在 CSS 中消失；列表中只有「当前 / 到期复习」才出现黄色面积。
- [ ] 23.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 S-8 走查；截图走查范围＝试卷列表页（含空态插画 + 满宽主按钮）。

## 24. hub 首页与卡片信息层级 （spec「Workspace card information hierarchy」）

- [ ] 24.1 hub 布局改「**最近使用置顶 + 网格**」：现状是 22 张**完全等权**的卡片、无排序无分组；重排为最近用的 4 个置顶大卡、其余在下方网格。验证：置顶区与网格区可辨；4 张置顶卡的数据来源可追溯；hub 仍为只读目录、零新增请求。
- [ ] 24.2 卡片信息层级：工作区名 22px 最大；知识点数 / 题目数 / 到期复习数三个计数 13px 一行排开，每个计数前一个小色点（色取自三角色）；**圆点是该计数的冗余状态通道，数字仍在文字中可读**。验证：字号与色点可辨；三个计数在灰度下仍可区分；计数含义与原实现一致。
- [ ] 24.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 S-1 走查；截图走查范围＝hub 首页（含空态）。

## 25. Agent 右栏 （spec「Agent rail presentation keeps the learning page primary」）

- [ ] 25.1 会话列表**补滚动容器 + 分组**：现状 `#ai-session-list`（`workbench.css:611`）无滚动容器（`overflow:visible` + 祖先 `overflow:hidden` ⇒ 被静默裁掉）；补内部滚动容器，并按「今天 / 昨天 / 更早」分组，每组小标题 + 组内圆角小块（标题 + provider 圆点 + 日期）。验证：长列表可滚到末条且不再被裁；三组结构成立。
- [ ] 25.2 消息流改**圆角卡片流**：每条消息一张圆角卡（Agent 消息可展开详情）；**不得演化成常驻任务面板**（既有 spec：右栏不取代中栏学习面）；Agent 长文挂 `.wb-reading`。**A-23：用户消息（用户在对话里的话）的底色改「沉底 `--surface-sunken`」（浅底深字），不再用近黑墨块**；Agent 消息仍是卡级纸面；两者靠「底色差 + 1px 内发丝线」分开。验证：卡片流可滚且无常驻面板；长文排版与知识点正文同层；**用户消息与 Agent 消息一眼可分**（两主题）。
- [ ] 25.3 composer、执行计划与活动浮层：composer 贴底、大圆角、聚焦变蓝 + 轻微抬起，且**随输入增高**（不把对话换成任务面板）；执行计划改**圆点时间线**（圆点 + 细线 + 文字），工具调用折叠成 ≤240 字摘要（展开看详情）；活动浮层改右上角圆角小卡，可收起、活动结束即消失，**空闲时不得留下任何辅助工作面**挡住中栏；窄屏抽屉保持「会话列表 + 消息 + composer」同一结构。验证：输入多行时 composer 增高且消息区不被替换；摘要长度受限；空闲时中栏不被遮挡；抽屉里 composer 仍可达。
- [ ] 25.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §3.4（会话列表可滚动）+ §1 S-11 走查；截图走查范围＝Agent 右栏（会话列表 / 消息流 / composer / 执行计划 / 活动浮层）；确认右栏交互的请求序列与载荷未变。

## 26. 文案清理 （spec「Interface copy voice」+ decisions 17.4）

- [ ] 26.1 按 `design-notes/copy-table.md` 执行全站文案定稿：**一个中文语气**、一个标签 / 一句话里不混中英；空态 = 插画 + 一句 + 满宽主按钮（按钮文案即动作）。验证：逐页核对 copy-table 的「改前 → 改后」条目全部落地；页面上无中英混排标签残留；改动前后语义逐条核对。
- [ ] 26.2 少字原则删注释：能删的界面注释**直接删除**（不是换成更漂亮的说明文字）；改造后界面上的说明性文字**数量不增加**。验证：交付一张删除前后信息量核对表，逐条说明删除理由；界面文字条数对比不增。
- [ ] 26.3 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §1 的「文字内容除文案清理项外应逐字一致」走查；同步 `docs/PRODUCT-MANUAL.md` 对应章节（本组改了用户可见文案）。

## 27. 契约漂移登记（`contract-drift.md`） （design.md D-15）

- [x] 27.1 新建 `openspec/changes/workbench-visual-language-v2/contract-drift.md`（**本变更目录下的工件，随本变更一起归档；不进 `docs/`**）：表头固定为 `ID | 位置（file:line） | 现状 | 与哪份契约冲突 | 建议归属 | 优先级`，ID 用 `CD-001` 递增，「建议归属」取值限 `openspec change` / `docs/DATA_MODEL.md` / `docs/GLOSSARY.md` / `spec delta` / `产品决策`。验证：文件存在于变更目录；`docs/` 下无同名文件；`docs/audits/` 与 `docs/PENDING-DEFINITIONS.md` 未被污染（漂移是行为 / 字段 / 口径分歧，不是名词缺失）。
- [x] 27.2 登记 **174 处**契约漂移：每条必须**能转成一个后续 change**，写清「改成什么」或「谁来定」；已知必含项至少包括 —— 建议行与每日计划队列有词条但无界面出口、「准确率」被记录中心打印但未在词表定义且被列为 `_Avoid_`、完成练习数受最近 100 轮限制而作答次数无上限、契约外绿（权威表无 token 名）的局部例外（`workbench.css:1211` / `:1214` / `:1462` / `:1892`）—— **已由 A-20-3 裁决：答对不再用绿，本轮整体移除（改中性墨 `--ink-strong` + 勾形几何，答错 = `--role-red`）**，**「连续学习天数」无现成数据源**（第 5 组 5.2b 已选，但 `workbench/` 下 `streak` / `consecutive` / 连续 命中 0，无字段无查询；口径未定义前**不得**由实现期自行发明算法，需所有者定义：哪些行为算「学习日」/ 断一天是否清零 / 跨时区如何取日）。⚠️ 两项**已在本轮裁决、不再算漂移**：① 动效偏好是否覆盖系统 reduced-motion —— 所有者裁决 A-2 定「显式选择优先」，两份 delta 已按此对齐（`workbench-ui` delta 改写完毕；措辞冲突仅作备查留档）；② 阅读面 stem 字号 —— 所有者裁决 A-6 定「题面与正文同档 17px / 1.75 / 38em」，design.md D-5 已按此修正。**表行数 = 174（`CD-001`…`CD-174`）**，比初估的 128 多 46 条，原因见 `contract-drift.md` §4.1：① **同一漂移的多条腿要逐腿登记**（每条腿的修复位置与责任人不同）；② 同一实现事实与两份契约冲突时按「契约侧腿」单列；③ **裁决已下但工件未改**的（A-9 / A-11 / A-15 / A-16 / A-17）按硬规则也必须登记。**登记册宁可多不可缺** —— 缺一条就等于漏一个已知缺陷，**不得**为凑数截断回 128。验证：表行数 = 174（`CD-001`…`CD-174`）；每行「建议归属」与「改成什么 / 谁来定」非空。
- [x] 27.3 交接提示与滚动维护责任：在 `docs/PENDING-DEFINITIONS.md` 或交接文档里显式提示「**存在 174 条已登记漂移**」，并写明登记表的清理责任人与滚动维护方式；**不得**把登记表当成「已处理」。验证：提示文本存在；登记表随本变更一起归档。
- [ ] 27.4 阶段验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）；按 `acceptance.md` §0（冻结线未被顺手改动）走查；截图走查范围＝无（文档任务）；确认本组**只登记、不动实现**。

## 28. 契约同步与最终验收 （AGENTS.md 契约协调 + D-15）

- [x] 28.1 `docs/GLOSSARY.md`：核对「柔和蒙德里安 / Soft Mondrian」条目已被改写为**暖色 + 现代圆润**定义（不再把「暖纸色 + 深色结构线」写成该语言的定义），并核对 13 条新词条齐全（纸面层级、夜纸、冗余状态通道、主题偏好、阅读字面、动效偏好、声音偏好、工作台设置视图、静物插画、台灯转场、少字原则、图案适配原则 + 静物插画）；与本清单用词逐条一致。验证：逐条核对，无缺项、无旧措辞残留。
- [x] 28.2 `docs/PRODUCT-MANUAL.md`：补「工作台设置视图」章节（含「按工作区存储、跨工作区独立、换工作区要重设外观」这条定案）与文案清理后的操作说明；**保留**知识点正文「宽行距 + 单侧结构线」的既有硬性表述；并按最终实现写明阅读面字号刻度。验证：章节齐全且未与既有条目冲突。
- [x] 28.3 `docs/ACTION-GRAPH.md` + `docs/action-graph/L3-actions.md`：登记新增动作（设置视图、主题切换、连对升级反馈）、退役动作（scope-tray 死预留与死 CSS 清理）、改级动作（`.rich-text` → `.wb-reading`）。验证：新增 / 退役 / 改级动作全部留痕。
- [x] 28.4 `docs/ARCHITECTURE.md`：更新静态资产目录结构（新增 `assets/icons/`、`assets/illustrations/`、`assets/audio/`、`fonts/`）与设置视图路由；并把「普通 Paper 题目与知识正文共享主阅读层级」这条既有契约标注为**已兑现**（此前两侧渲染器层级不一致）。验证：文档里的目录树与仓库实际一致。
- [x] 28.5 spec 补正与冲突收敛：把 D-14 的 5 档日历阈值（0 / 1 / 2–3 / 4–7 / ≥8，源自 `records.py:237`）写进 `specs/workbench-ui/spec.md` 的 Records center 需求（或按 AGENTS.md 登记为独立 change），并补 `.level-0` 的 CSS 与页面图例；同时**核对** `design.md` D-5 与 spec delta 关于 stem 字号的表述**一致**（题面与正文同为 **17px / 1.75 / 38em** —— 所有者裁决 A-6 的结论；`design.md` D-5 已按 A-6 修正，早年的「题面 16px / 1.70 / 42em」冲突**已不存在**，本条是**一致性核对**而非「冲突校正」）。验证：阈值成为可见契约（CSS + 图例 + 规格三处一致）；`design.md` D-5 与 spec delta 的 stem 字号三档数值（17px / 1.75 / 38em）逐项相同。
- [ ] 28.6 最终验收：跑 AGENTS.md 四条验证命令（`python -m pytest tests -q` / `python -m compileall -q lessonkit.py workbench pipeline pool tests` / `openspec validate --specs --strict` / `python lessonkit.py guard extract-problems --course dmath --chapter ch06`）并贴输出；`openspec validate --specs --strict` 全绿；按 `acceptance.md` §1 补齐铺开段新增页面对应的对照截图（S-1 / S-8 / S-11）与 §3 增补项；确认**图谱页逐像素零变化、请求与持久化零变化、池 schema 零变更**；确认第 27 组的漂移登记表随变更归档。

## 29. 实物插画精修（所有者追加：瓶 / 地球仪 / 书本等实物组件不够精致）

> 触发：所有者看了已入库的 10 张空态插画与台灯，判断「不够精致」。
> **权威仍是 `design-notes/asset-spec.md`** —— 本组不是「重画」，是**把实现贴回规格** +
> 补规格没写死的「可辨认度」与「跨图一致性」。

- [ ] 29.1 **建机检闸门** `tools/audit-assets.py`：逐张量 `getBBox()` 与 `asset-spec.md` §3.12 的实测表比对（容差 ±2 u），并查 §1.1–§1.6 / §3.0 的技术条款（viewBox · 根上无 width/height · 端点连接 round · 线宽 3:2:1.5 阶梯且不超三档 · 无 SVG filter · 淡彩用预混色不用 alpha · 四个语义组齐全 · 桌面横线 y=168 且长 144–168 u · 高光 ≤2 · 阴影不透明度 ≤12% · 延伸元素必须带 `asset-empty__extension`）。验证：`python tools/audit-assets.py --strict` 退出码 0。
- [ ] 29.2 **修掉 §3.12 的实测偏差**：`empty-vase`（最长边 131.1 u 超上限 ⇒ 缩到 ≤132 u 口径内或按上限重画）· `empty-fruit-basket`（上缘偏 5.8 u）· `empty-pencil-cup`（左右各偏 4 u、离横线 164.6 u 未压到 165–168）· `empty-cup` 的蒸汽按 `asset-empty__extension` 归组（否则量到 44 u 偏差）· `empty-vase` 的花枝同上。验证：`audit-assets.py` 全部通过。
- [ ] 29.3 **可辨认度**（清单 `3.6-4`「插画是**具象器物**，不是抽象几何块」）：`empty-compass` 现在读起来像**三脚架/旗杆**、`empty-canvas` 像**镜子**、`empty-globe` 的支架与球体网格不对称 —— 逐张改成**一眼能叫出名字**的器物。验证：三张渲染图旁边写得出正确名称（人工判读）。
- [ ] 29.4 **跨图一致性**：十张并排时**同一张桌子**（桌面横线 y=168 齐平）· **视觉重量相当**（最长边极差 ≤1.6 倍）· 同一支笔（端点圆角一致、线宽同档）· 每张都有淡彩与高光（不许有的一张是纯线稿）。验证：十张并排渲染图（`tmp/asset-shots/grid.png` 那种）+ 逐条对应 audit 的检查项。
- [ ] 29.5 **双主题**：同一份文件在暖纸 / 夜纸下**都成立**（淡彩走 `--asset-wash-*` 与 `color-mix`，线稿墨色夜纸自动反相）。验证：夜纸渲染图。
- [ ] 29.6 阶段验收：跑 AGENTS.md 四条验证命令；`python tools/audit-assets.py --strict` 退出码 0；十张 + 台灯 + 五个图标的并排渲染图交出；**清单 `3.6-4` 由人工判读**。

---

## Self-check

- [ ] 所有任务都是 `- [ ] X.Y` 复选框格式
- [ ] 编号连续、无重复（X 为组号，Y 在组内从 1 连续排到该组验收任务）
- [ ] 每条任务可验证（能看出改哪个文件、做什么、怎么算做完）
- [ ] 样板线与铺开两段之间有明确分界（`## 第一段：样板线` 第 1–22 组 / `## 第二段：铺开` 第 23–28 组；22.4 是用户验收关卡）
- [ ] 覆盖 design.md D-1…D-15 全部十五条决策，每条至少一条任务
- [ ] 第 5 组 5.2b「进度与成就的可见反馈」已落点：18.5（章节知识点计数）+
      19.4（记录中心累计量 + 连续学习天数待确认）+ 27.2（漂移登记）+
      `specs/workbench-ui/spec.md` 的新增 Requirement（ADDED 15 条）
- [ ] **`decisions.md` A-27.2 的 M-F…M-N 已落成实现任务**（每条首类 Requirement 都有对应组）：
      交卷庆祝分两层（M-F / M-G）→ **8.8**（keyframes 与数字滚动）+ **16.7**（完成页承载位）+
      **17.6**（里程碑判定两条件：全对 / 章节首次完成）+ **17.7**（爆点与彩带 / 纸片）；
      台灯主题转场（M-L）→ **8.7**（四段实现）+ **12.5**（夜纸取值与层级检查）；
      连对升级（M-H / M-I / M-J / M-K）→ **17.1 / 17.2 / 17.8**（三级计数器 / 一份参数化横幅 / 火苗簇与负反馈）；
      视图转场与骨架屏（M-D / M-E）→ **21.1 / 21.5**（容器动画约束，含「整体替换 innerHTML ⇒ 必须容器动画」）+
      **21.6**（降级终态一致）；
      关键反馈音效（M-N）→ **10.1 / 10.5 / 10.6**（资产 / 四个触发点 / 声画同步）；
      动效偏好与分级降级（M-M）→ **8.9**（终态一致铁律）+ **11.6**（A-2 语义）
- [ ] 动效验收已进关卡：**22.6**（动效分镜条，对应 `acceptance.md` §2 的 M-1…M-13）+
      **22.7**（每条动效的 reduced-motion 降级对照帧，终态与开启时一致）+ **22.8**（动效关卡，缺一条分镜条即 FAIL）
- [ ] 覆盖三份 spec delta 的每条 Requirement（含 workbench-settings 7 条、calendar-workload 1 条）
- [ ] 每组有验收任务，含 AGENTS.md 的四条验证命令 + `acceptance.md` 对应小节
- [ ] 新增测试任务存在（D-6 的 `tests/test_markdown_render_parity.py`）
- [ ] 新增登记任务存在（D-15 的 `contract-drift.md`，写清 128 处）
- [ ] SVG 资产（第 9 组）与音效资产（第 10 组）单列为可独立验收的任务组
- [ ] 没有引入构建步骤、npm 或新框架
- [ ] 知识图谱页零改动约束已落到具体任务（1.2 / 12.2 / 22.1 G-5 / 28.6），且已按 `decisions.md` A-8 移交 `graph-node-visual-language`（本变更不触碰图谱）
- [ ] 未修改任何产品代码（本文只落 `tasks.md`）
